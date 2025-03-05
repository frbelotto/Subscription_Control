import pytest

from subscription_control.content_providers.content_providers import create_content_provider, delete_content_provider, list_content_provider
from subscription_control.schemas import SchemaContentProviderBase

@pytest.fixture
def valid_content_provider():
    return SchemaContentProviderBase(
        name='test_provider',
        description='test description',
        api_engine_module_name='test.py',
        email='test@example.com',
    )

@pytest.mark.asyncio
async def test_create_content_provider(valid_content_provider):
    """
    Test creating a content provider.
    """
    content = valid_content_provider
    result = await create_content_provider(content)
    assert isinstance(result, dict) is False
    assert result.name == content.name
    assert result.description == content.description
    assert result.email == content.email
    assert result.api_engine_module_name == content.api_engine_module_name

@pytest.mark.asyncio
async def test_create_content_provider_duplicate():
    """
    Test creating a duplicate content provider.
    """
    content = SchemaContentProviderBase(
        name='PokeApi',
        description='Free PokeApi database',
        api_engine_module_name='PokeApi.py',
        email='teste@teste.com',
    )
    from sqlalchemy.exc import IntegrityError

    await create_content_provider(content)
    try:
        await create_content_provider(content)
    except IntegrityError as e:
        assert isinstance(e, IntegrityError)
    else:
        assert False, 'IntegrityError not raised'

@pytest.mark.asyncio
async def test_list_content_provider():
    """
    Test listing content providers.
    """
    content1 = SchemaContentProviderBase(
        name='PokeApi',
        description='Free PokeApi database',
        api_engine_module_name='PokeApi.py',
        email='pokeapi@teste.com',
    )
    content2 = SchemaContentProviderBase(
        name='WeatherApi',
        description='Weather data provider',
        api_engine_module_name='WeatherApi.py',
        email='weatherapi@teste.com',
    )
    await create_content_provider(content1)
    await create_content_provider(content2)
    result = await list_content_provider()
    assert isinstance(result, list) is True
    assert len(result) >= 2  # Usando >= para ser mais resiliente
    # Check for specific fields in the content providers
    for provider in result:
        assert hasattr(provider, 'name')
        assert hasattr(provider, 'description')
        assert hasattr(provider, 'email')
        assert hasattr(provider, 'api_engine_module_name')

@pytest.mark.asyncio
async def test_list_content_provider_with_filters():
    """
    Test listing content providers with filters.
    """
    content1 = SchemaContentProviderBase(
        name='PokeApi',
        description='Free PokeApi database',
        api_engine_module_name='pokeapi.py',
        email='pokeapi@teste.com',
    )
    content2 = SchemaContentProviderBase(
        name='WeatherApi',
        description='Weather data provider',
        api_engine_module_name='WeatherApi.py',
        email='weatherapi@teste.com',
    )
    await create_content_provider(content1)
    await create_content_provider(content2)
    result = await list_content_provider(name='PokeApi')
    assert isinstance(result, list) is True
    assert len(result) >= 1
    assert result[0].name == 'pokeapi'  # type: ignore

@pytest.mark.asyncio
async def test_should_filter_providers_case_insensitive(valid_content_provider: SchemaContentProviderBase):
    """
    Test case-insensitive filtering of content providers.
    """
    await create_content_provider(valid_content_provider)
    result = await list_content_provider(name='TEST_PROVIDER')
    assert len(result) >= 1
    assert any(provider.name.lower() == valid_content_provider.name.lower() for provider in result)

@pytest.mark.asyncio
async def test_delete_content_provider(valid_content_provider):
    """
    Test deleting a content provider.
    """
    created_content = await create_content_provider(valid_content_provider)
    result = await delete_content_provider(created_content.id)
    assert result == {'message': 'Content provider deleted successfully'}

@pytest.mark.asyncio
async def test_delete_content_provider_not_found():
    """
    Test deleting a non-existent content provider.
    """
    result = await delete_content_provider(999)
    assert result == {'error': 'Content provider not found'}

@pytest.mark.asyncio
async def test_delete_content_provider_existing_data():
    """
    Test deleting a content provider with existing data.
    """
    content = SchemaContentProviderBase(
        name='existing_provider',
        description='existing description',
        api_engine_module_name='existing.py',
        email='existing@example.com',
    )
    created_content = await create_content_provider(content)
    result = await delete_content_provider(created_content.id)
    assert result == {'message': 'Content provider deleted successfully'}

    # Verify the content provider is deleted
    result = await list_content_provider(name='existing_provider')
    assert len(result) == 0

# Novos testes adicionados:

@pytest.mark.asyncio
async def test_list_content_provider_multiple_filters():
    """
    Test listing content providers with multiple filters simultaneously.
    """
    # Create unique test content providers
    content = SchemaContentProviderBase(
        name='MultiFilterTest',
        description='Testing multiple filters',
        api_engine_module_name='multifilter.py',
        email='multi@filter.com',
    )
    await create_content_provider(content)
    
    # Test with multiple filters that should match
    result = await list_content_provider(
        name='multifilter',
        description='multiple',
        email='multi@filter.com'
    )
    assert len(result) >= 1
    assert all(provider.name.lower() == 'multifiltertest' for provider in result)
    
    # Test with filters that shouldn't match anything
    result = await list_content_provider(
        name='multifilter',
        description='nonexistent text'
    )
    assert len(result) == 0

@pytest.mark.asyncio
async def test_list_content_provider_empty_result():
    """
    Test listing content providers with filters that should return empty list.
    """
    result = await list_content_provider(name='ThisProviderShouldNotExist12345')
    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.asyncio
async def test_create_content_provider_input_validation():
    """
    Test input validation when creating content providers.
    """
    from pydantic import ValidationError
    
    # Test with invalid email
    with pytest.raises(ValidationError):
        invalid_content = SchemaContentProviderBase(
            name='InvalidEmail',
            description='Testing invalid email',
            api_engine_module_name='invalid.py',
            email='not-an-email',  # This should cause validation error
        )

@pytest.mark.asyncio
async def test_create_content_provider_whitespace_handling():
    """
    Test that whitespace is handled correctly in content provider data.
    """
    content = SchemaContentProviderBase(
        name='  Whitespace  Test  ',  # Extra spaces should be stripped
        description='  Description with spaces  ',
        api_engine_module_name='whitespace.py',
        email='whitespace@test.com',
    )
    
    result = await create_content_provider(content)
    assert result.name == 'whitespace  test'  # Should be stripped and lowercased
    assert result.description == 'description with spaces'  # Should be stripped and lowercased

@pytest.mark.asyncio
async def test_list_content_provider_by_id():
    """
    Test listing content providers by ID.
    """
    # Create a content provider and get its ID
    content = SchemaContentProviderBase(
        name='IdTest',
        description='Testing ID filtering',
        api_engine_module_name='idtest.py',
        email='id@test.com',
    )
    created = await create_content_provider(content)
    
    # Retrieve by ID
    result = await list_content_provider(id=created.id)
    assert len(result) == 1
    assert result[0].id == created.id
    assert result[0].name == created.name.lower()
