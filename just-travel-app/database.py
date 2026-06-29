
import os
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import JSON, Column

# Configure logging
logger = logging.getLogger(__name__)

# Database Configuration - configurable via environment variable
# SQLite: sqlite+aiosqlite:///./just_travel.db
# PostgreSQL: postgresql+asyncpg://user:pass@host:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./just_travel.db")

# --- Data Models ---

class User(SQLModel, table=True):
    """
    Represents a registered user (Local or OAuth).
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None) # Null for OAuth users
    full_name: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    provider: str = Field(default="local") # local, google
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    itineraries: List["Itinerary"] = Relationship(back_populates="user")


class Itinerary(SQLModel, table=True):
    """
    Stores generated itineraries and creative assets.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    destination: str
    summary: str
    
    # Fix: Use default_factory=dict for mutable defaults
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    creative_assets: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Phase 3: Background Task Media Generation
    poster_url: Optional[str] = None
    video_url: Optional[str] = None
    media_status: str = "pending"  # pending | generating | completed | failed
    media_task_id: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: User = Relationship(back_populates="itineraries")


# --- Engine & Session ---

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Fix: Create sessionmaker once at module level
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """
    Initialize the database tables.
    """
    logger.info("Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database initialized.")

async def get_session() -> AsyncSession:
    """
    Dependency for FastAPI routes to get a database session.
    """
    async with async_session_maker() as session:
        yield session
