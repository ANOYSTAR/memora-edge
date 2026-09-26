"""
Memora-Edge — FastAPI Backend
Main application with all API routes for chat, voice, memory, search, and sync.
"""
import json
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from config import OLLAMA_HOST, OLLAMA_MODEL, app_state
from database import init_db

# Import agents
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.memory_agent import MemoryAgent
from agents.retrieval_agent import RetrievalAgent
from agents.classification_agent import ClassificationAgent
from agents.sync_agent import SyncAgent
from agents.voice_agent import VoiceAgent


# === Agent Singletons ===
memory_agent = MemoryAgent()
retrieval_agent = RetrievalAgent()
classification_agent = ClassificationAgent()
sync_agent = SyncAgent()
voice_agent = VoiceAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and agents on startup."""
    await init_db()
    await memory_agent.initialize()
    await sync_agent.initialize()
    yield
    await classification_agent.close()


app = FastAPI(
    title="Memora-Edge API",
    description="Offline-first AI assistant with on-device semantic memory",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Request / Response Models ===

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    remember: bool = True

class ChatResponse(BaseModel):
    response: str
    memory_id: Optional[str] = None
    classification: Optional[dict] = None
    context_memories: list = []

class RememberRequest(BaseModel):
    text: str
    source: str = "manual"
    importance: Optional[str] = None
    privacy: Optional[str] = None
    category: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    category: Optional[str] = None
    importance: Optional[str] = None
    privacy: Optional[str] = None
    min_score: float = 0.0

class SyncRequest(BaseModel):
    memory_ids: Optional[List[str]] = None
    sync_all: bool = False

class ConnectionToggle(BaseModel):
    online: Optional[bool] = None


# === Chat API ===

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI assistant.
    1. Retrieve relevant memories for context
    2. Generate response via Ollama
    3. Optionally store the interaction as a memory
    """
    # Step 1: Retrieve relevant memories
    context_memories = retrieval_agent.search_local(
        request.message, limit=3, min_score=0.3
    )
    
    # Build context from memories
    memory_context = ""
    if context_memories:
        memory_context = "\n\nRelevant memories:\n"
        for mem in context_memories:
            memory_context += f"- [{mem['category']}] {mem['text']} (relevance: {mem['score']})\n"
    
    # Step 2: Generate response via Ollama
    system_prompt = f"""You are Memora, a helpful AI assistant with persistent memory.
You remember past conversations and can recall them when relevant.
You are running locally on the user's device — their data never leaves without permission.
Be concise, helpful, and reference relevant memories when appropriate.
{memory_context}"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": request.message,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 512,
                    }
                }
            )
            response.raise_for_status()
            ai_response = response.json().get("response", "I'm thinking...")
    except Exception as e:
        ai_response = f"I'm currently running in offline mode. I've stored your message and will process it fully when connected to the local LLM. Error: {str(e)[:100]}"
    
    # Step 3: Classify and store memory
    memory_id = None
    classification = None
    
    if request.remember:
        classification = await classification_agent.classify(request.message)
        
        memory_data = await memory_agent.store_memory(
            text=request.message,
            source="chat",
            importance=classification["importance"],
            importance_score=classification["importance_score"],
            privacy=classification["privacy"],
            category=classification["category"],
        )
        memory_id = memory_data["id"]
        
        # Auto-queue for sync if allowed
        if classification["privacy"] == "sync_allowed":
            await sync_agent.queue_for_sync(memory_id)
    
    return ChatResponse(
        response=ai_response,
        memory_id=memory_id,
        classification=classification,
        context_memories=context_memories,
    )


# === Voice API ===

@app.post("/voice")
async def voice_chat(audio: UploadFile = File(...)):
    """
    Voice chat pipeline:
    1. Transcribe audio via Faster Whisper
    2. Process through chat pipeline
    3. Return text response (+ TTS audio if available)
    """
    audio_bytes = await audio.read()
    
    # Transcribe
    transcription = await voice_agent.transcribe(audio_bytes)
    
    if not transcription.get("text"):
        return {
            "transcription": transcription,
            "response": "I couldn't understand the audio. Please try again.",
            "error": transcription.get("error"),
        }
    
    # Process through chat
    chat_request = ChatRequest(message=transcription["text"], source="voice")
    chat_response = await chat(chat_request)
    
    # Synthesize response
    tts_audio = await voice_agent.synthesize(chat_response.response)
    
    return {
        "transcription": transcription,
        "response": chat_response.response,
        "memory_id": chat_response.memory_id,
        "classification": chat_response.classification,
        "has_audio": tts_audio is not None,
    }


@app.post("/voice/tts")
async def text_to_speech(text: str = Query(...)):
    """Convert text to speech and return audio."""
    audio_bytes = await voice_agent.synthesize(text)
    if audio_bytes:
        return Response(content=audio_bytes, media_type="audio/wav")
    raise HTTPException(status_code=503, detail="TTS not available")


# === Memory API ===

@app.post("/remember")
async def remember(request: RememberRequest):
    """
    Store a new memory with automatic classification.
    """
    # Classify if not all labels provided
    if not all([request.importance, request.privacy, request.category]):
        classification = await classification_agent.classify(request.text)
        importance = request.importance or classification["importance"]
        importance_score = classification["importance_score"]
        privacy = request.privacy or classification["privacy"]
        category = request.category or classification["category"]
    else:
        importance = request.importance
        importance_score = 0.5
        privacy = request.privacy
        category = request.category
    
    memory_data = await memory_agent.store_memory(
        text=request.text,
        source=request.source,
        importance=importance,
        importance_score=importance_score,
        privacy=privacy,
        category=category,
    )
    
    # Auto-queue for sync
    if privacy == "sync_allowed":
        await sync_agent.queue_for_sync(memory_data["id"])
    
    return {
        "status": "stored",
        "memory": memory_data,
    }


@app.get("/memories")
async def get_memories(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get all memories with pagination."""
    memories = await memory_agent.get_all_memories(limit=limit, offset=offset)
    stats = await memory_agent.get_stats()
    return {
        "memories": memories,
        "stats": stats,
        "count": len(memories),
        "limit": limit,
        "offset": offset,
    }


@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory."""
    memory = await memory_agent.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory."""
    success = await memory_agent.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "memory_id": memory_id}


# === Search API ===

@app.post("/search")
async def search(request: SearchRequest):
    """Semantic search across memories."""
    results = retrieval_agent.search_local(
        query=request.query,
        limit=request.limit,
        category=request.category,
        importance=request.importance,
        privacy=request.privacy,
        min_score=request.min_score,
    )
    return {
        "query": request.query,
        "results": results,
        "count": len(results),
    }


# === Sync API ===

@app.post("/sync")
async def sync(request: SyncRequest):
    """Sync memories to cloud."""
    if request.sync_all:
        # Auto-queue all eligible memories first
        queue_result = await sync_agent.auto_queue_all()
    
    # Sync pending
    result = await sync_agent.sync_pending()
    return result


@app.get("/sync/status")
async def sync_status():
    """Get synchronization status."""
    return await sync_agent.get_sync_status()


# === Connection API ===

@app.post("/connection/toggle")
async def toggle_connection(request: ConnectionToggle):
    """Toggle online/offline mode for demo."""
    if request.online is not None:
        app_state.is_online = request.online
    else:
        app_state.toggle_connection()
    
    return {
        "is_online": app_state.is_online,
        "message": f"Connection {'online' if app_state.is_online else 'offline'}",
    }


@app.get("/connection/status")
async def connection_status():
    """Get current connection status."""
    return {"is_online": app_state.is_online}


# === Dashboard API ===

@app.get("/dashboard")
async def dashboard():
    """Get dashboard statistics."""
    stats = await memory_agent.get_stats()
    sync_status_data = await sync_agent.get_sync_status()
    
    return {
        "memories": stats,
        "sync": sync_status_data,
        "is_online": app_state.is_online,
        "timestamp": datetime.utcnow().isoformat(),
    }


# === Health ===

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "memora-edge",
        "version": "1.0.0",
        "is_online": app_state.is_online,
    }
