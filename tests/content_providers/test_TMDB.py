import pytest

from subscription_control.content_providers.tmdb import ApiProvider
from subscription_control.schemas import SchemaContentProviderBase, SchemaProductBase
from subscription_control.content_providers.content_providers import create_content_provider

@pytest.fixture
async def content_provider():
    provider = SchemaContentProviderBase(
        name='TMDB',
        description='TMDB API',
        api_engine_module_name='tmdb.py',
        email='teste@teste.com'
    )
    await create_content_provider(provider)
    return provider

@pytest.mark.asyncio
async def test_get_content(tmdb_api_provider):
    """Test if the API returns the correct number of movies"""
    await tmdb_api_provider.get_content(10)

    assert tmdb_api_provider.results is not None
    assert len(tmdb_api_provider.results) > 0
    assert len(tmdb_api_provider.results) == 10
    # Check for specific fields in the results
    for movie in tmdb_api_provider.results:
        assert 'title' in movie
        assert 'id' in movie

@pytest.mark.asyncio
async def test_standardize_content(tmdb_content_provider, tmdb_api_provider):
    """Test if the content is properly standardized to SchemaProductBase format"""
    # Removed await as tmdb_content_provider is not an awaitable object
    tmdb_content_provider
    data = await tmdb_api_provider.standardize_content(10)

    assert isinstance(data, list)
    assert all(isinstance(item, SchemaProductBase) for item in data)
    assert len(data) == 10

    # Validate first item structure
    first_item = data[0]
    assert isinstance(first_item.ext_id, str)
    assert isinstance(first_item.name, str)
    assert isinstance(first_item.value, (int, float))
    assert isinstance(first_item.description, str)
    assert first_item.image is not None


@pytest.mark.asyncio
async def test_should_validate_standardized_content_structure(tmdb_content_provider, tmdb_api_provider):
    """Test if standardized content has all required fields with correct types"""
    tmdb_content_provider
    data = await tmdb_api_provider.standardize_content(limit=10)

    product = data[0]
    assert hasattr(product, 'name')
    assert hasattr(product, 'description')
    assert hasattr(product, 'value')
    assert isinstance(product.value, (int, float))
    assert product.value > 0
    assert len(product.name) > 0
    assert len(product.description) > 0
