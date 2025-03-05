from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from subscription_control.settings import Settings

settings = Settings()

# Configurações para banco de dados síncrono
if settings.DATABASE_URL is None:
    raise ValueError('DATABASE_URL is not set in the environment variables')

sync_engine = create_engine(settings.DATABASE_URL, echo=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

async_engine = create_async_engine(settings.DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///'), echo=False)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """
    Context manager for synchronous database sessions.

    Yields:
        Session: A SQLAlchemy session instance
    """
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for asynchronous database sessions.

    Yields:
        AsyncSession: An async SQLAlchemy session instance
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_session(async_mode: bool = False):
    """
    Factory function to get appropriate session based on mode.

    Args:
        async_mode (bool): If True, returns async session, otherwise sync session

    Returns:
        Context manager for database session
    """
    return get_async_session() if async_mode else get_sync_session()
