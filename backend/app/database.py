"""Async SQLAlchemy engine and session factory."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def get_engine():
    """Create async engine from settings."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
    )


def get_session_factory(engine=None):
    """Create async session factory."""
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides database session."""
    engine = get_engine()
    session_factory = get_session_factory(engine)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
