"""
Memora-Edge Database Layer
SQLite schema and async session management for memory metadata.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Float, DateTime, Boolean, Text, Integer,
    create_engine, event
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL, SQLITE_DB_PATH


class Base(DeclarativeBase):
    pass


class Memory(Base):
    """Core memory record stored in SQLite."""
    __tablename__ = "memories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source: Mapped[str] = mapped_column(String(50), default="chat")  # chat, voice, manual
    importance: Mapped[str] = mapped_column(String(20), default="medium")  # critical, high, medium, low
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    privacy: Mapped[str] = mapped_column(String(20), default="sync_allowed")  # local_only, sync_allowed
    category: Mapped[str] = mapped_column(String(50), default="personal")  # personal, work, maintenance, research, health
    synced: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    embedding_stored: Mapped[bool] = mapped_column(Boolean, default=False)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class SyncQueueItem(Base):
    """Queue item for pending synchronization."""
    __tablename__ = "sync_queue"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    memory_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, syncing, synced, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ConversationMessage(Base):
    """Chat conversation history."""
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    session_id: Mapped[str] = mapped_column(String(36), default="default")
    has_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)


# Async engine and session
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Get an async database session."""
    async with async_session() as session:
        yield session
