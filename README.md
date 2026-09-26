# 🧠 Memora-Edge

**Your AI Remembers. Even Offline.**

> Team: Grey Coder | Paytm Hackathon

Memora-Edge is an offline-first AI assistant with on-device semantic memory powered by Qdrant Edge. It lets users chat with a local AI, speak using voice, store and retrieve memories by meaning, and synchronize selected data when connectivity returns — all without any paid APIs.

![Memora-Edge](https://img.shields.io/badge/Memora--Edge-v1.0-blue?style=for-the-badge)
![Offline First](https://img.shields.io/badge/Offline-First-green?style=for-the-badge)
![Qdrant Edge](https://img.shields.io/badge/Qdrant-Edge-purple?style=for-the-badge)

---

## ✨ Features

- 🤖 **AI Chat** — ChatGPT-like interface powered by local Ollama (Llama 3.2)
- 🎙️ **Voice Mode** — Push-to-talk with Faster Whisper + Piper TTS
- 🧠 **Semantic Memory** — Memories stored as vectors, retrieved by meaning
- 🔒 **Privacy First** — Sensitive memories never leave the device
- 📡 **Smart Sync** — Only approved memories sync when connectivity returns
- 📊 **Dashboard** — Real-time analytics with animated visualizations
- 🔍 **Memory Explorer** — Search, filter, and inspect stored memories
- 🌐 **Demo Mode** — Toggle offline/online to demonstrate capabilities

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Next.js UI │────▶│  FastAPI API  │────▶│  Qdrant Edge │
│  Port 3000  │     │  Port 8000   │     │  Port 6333   │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │   Agents     │
                    ├──────────────┤
                    │ Memory Agent │
                    │ Retrieval    │
                    │ Classifier   │
                    │ Sync Agent   │
                    │ Voice Agent  │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │   Storage    │
                    ├──────────────┤
                    │ SQLite (meta)│
                    │ Qdrant (vec) │
                    │ memory_vault/│
                    └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Option 1: Docker (Recommended)

```bash
# Clone the project
cd memora-edge

# Start everything
docker-compose up -d

# Pull the LLM model
docker exec memora-ollama ollama pull llama3.2

# Open browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt

# Start Qdrant (requires Docker)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Start Ollama
ollama serve
ollama pull llama3.2

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
memora-edge/
├── frontend/                 # Next.js 15 + TypeScript + Tailwind
│   └── src/
│       ├── app/             # Pages (dashboard, chat, voice, etc.)
│       ├── components/      # Reusable UI components
│       ├── lib/             # API client, utilities
│       └── stores/          # Zustand state management
├── backend/                  # FastAPI + Python
│   ├── main.py              # API routes
│   ├── config.py            # Configuration
│   └── database.py          # SQLite models
├── agents/                   # Independent AI agents
│   ├── memory_agent.py      # Store memories + embeddings
│   ├── retrieval_agent.py   # Semantic search
│   ├── classification_agent.py  # Auto-classify memories
│   ├── sync_agent.py        # Offline queue + cloud sync
│   └── voice_agent.py       # Whisper STT + Piper TTS
├── memory_vault/             # Local memory storage
│   ├── vectors/             # Qdrant data
│   ├── documents/           # Stored documents
│   ├── images/              # Stored images
│   └── audio/               # Voice recordings
├── sync_queue/               # Pending sync items
├── sqlite/                   # SQLite database
├── docker-compose.yml        # Docker orchestration
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Chat with AI assistant |
| POST | `/voice` | Voice-to-AI pipeline |
| POST | `/remember` | Store a new memory |
| POST | `/search` | Semantic memory search |
| GET | `/memories` | List all memories |
| POST | `/sync` | Sync memories to cloud |
| GET | `/sync/status` | Get sync status |
| POST | `/connection/toggle` | Toggle online/offline |
| GET | `/dashboard` | Dashboard analytics |

---

## 🎯 Demo Scenario

1. **Toggle OFF** internet in the Sync Center
2. **Speak**: "Remember that Generator 5 needs inspection tomorrow"
3. AI answers and stores locally with auto-classification
4. **Search**: "Which generator needs maintenance?"
5. AI retrieves the memory instantly via semantic similarity
6. **Toggle ON** internet
7. Watch pending memories animate into Cloud column
8. Dashboard updates in real time

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React, TypeScript, Tailwind CSS, ShadCN UI, Framer Motion, Zustand |
| Backend | FastAPI, Python 3.11 |
| Vector DB | Qdrant Edge |
| Metadata | SQLite |
| LLM | Ollama (Llama 3.2) |
| Embeddings | Sentence Transformers (bge-small-en-v1.5) |
| Voice STT | Faster Whisper |
| Voice TTS | Piper TTS |

---

## 📐 Memory Architecture

Each memory contains:
- UUID
- Original text
- Embedding vector (384-dim)
- Timestamp
- Source (chat/voice/manual)
- Importance (critical/high/medium/low)
- Privacy label (local_only/sync_allowed)
- Category (personal/work/maintenance/research/health)
- Sync status

Qdrant Edge stores vectors + metadata references.
SQLite stores structured metadata for filtering and analytics.

---

## 🔐 Privacy

- All data stays on-device by default
- `local_only` memories are never uploaded
- Only `sync_allowed` memories can be synced
- No external API calls for core functionality
- Cloud sync is simulated via a separate Qdrant collection

---

## 📜 License

MIT License — Built for Paytm Hackathon by Team Grey Coder
