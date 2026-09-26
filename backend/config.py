"""
Memora-Edge Configuration
Central configuration for all services and paths.
"""
import os
from pathlib import Path
from pydantic import BaseModel

# Base paths
BASE_DIR = Path(__file__).parent.parent
MEMORY_VAULT_DIR = BASE_DIR / "memory_vault"
SYNC_QUEUE_DIR = BASE_DIR / "sync_queue"
SQLITE_DIR = BASE_DIR / "sqlite"

# Ensure directories exist
for d in [
    MEMORY_VAULT_DIR,
    MEMORY_VAULT_DIR / "vectors",
    MEMORY_VAULT_DIR / "documents",
    MEMORY_VAULT_DIR / "images",
    MEMORY_VAULT_DIR / "audio",
    SYNC_QUEUE_DIR,
    SQLITE_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)

# Database
SQLITE_DB_PATH = SQLITE_DIR / "memories.db"
DATABASE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_LOCAL = "local_memory"
QDRANT_COLLECTION_CLOUD = "cloud_memory"

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = 384

# Voice
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")

# Sync
SYNC_BATCH_SIZE = 50
SYNC_INTERVAL_SECONDS = 30


class AppState:
    """Mutable application state for demo mode."""
    is_online: bool = True
    
    def toggle_connection(self) -> bool:
        self.is_online = not self.is_online
        return self.is_online

app_state = AppState()
