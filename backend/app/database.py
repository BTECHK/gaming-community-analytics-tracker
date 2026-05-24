"""Async SQLAlchemy engine and session factory."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


_engine = None
_session_factory = None


def get_engine():
    """Return the process-wide async engine, creating it once.

    The engine owns a connection pool and is meant to be a long-lived
    singleton. Creating a new engine per request/job (as this used to) leaks
    pooled connections until Postgres refuses new clients with
    "sorry, too many clients already".
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory(engine=None):
    """Return an async session factory.

    With no engine, returns the cached factory bound to the shared engine. An
    explicit engine (e.g. test fixtures) always yields a dedicated factory.
    """
    if engine is not None:
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
