import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from subscription_control.models import table_registry
from subscription_control.schemas import SchemaContentProviderBase
from subscription_control.content_providers.tmdb import ApiProvider as TmdbApiProvider
from subscription_control.content_providers.pokeapi import ApiProvider as PokeApiProvider
from subscription_control.content_providers.content_providers import create_content_provider

DB_URL = 'sqlite+aiosqlite:///:memory:'

@pytest_asyncio.fixture
async def async_session():
    """
    Fixture to create an asynchronous session for testing.
    """
    engine = create_async_engine(DB_URL, echo=False)
    async_session = sessionmaker(
        engine,  # type: ignore
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )  # type: ignore
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()

@pytest.fixture(autouse=True)
def set_global_session(monkeypatch, async_session):
    """
    Fixture to set the global session for testing.
    """
    monkeypatch.setattr('subscription_control.content_providers.content_providers.get_session', lambda async_mode=True: async_session)
    monkeypatch.setattr('subscription_control.content_providers.products_handler.get_session', lambda async_mode=True: async_session)
    monkeypatch.setattr('subscription_control.consumer.consumer_handler.get_session', lambda async_mode=True: async_session)


@pytest_asyncio.fixture
async def tmdb_content_provider():
    provider = SchemaContentProviderBase(
        name='TMDB',
        description='TMDB API',
        api_engine_module_name='tmdb.py',
        email='teste@teste.com'
    )
    await create_content_provider(provider)
    return provider

@pytest_asyncio.fixture
async def pokeapi_content_provider():
    provider = SchemaContentProviderBase(
        name='PokeApi',
        description='Free PokeApi database',
        api_engine_module_name='pokeapi.py',
        email='teste@teste.com',
    )
    await create_content_provider(provider)
    return provider

@pytest.fixture
def tmdb_api_provider():
    return TmdbApiProvider()

@pytest.fixture
def pokeapi_api_provider():
    return PokeApiProvider()
