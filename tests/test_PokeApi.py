import pytest

from subscription_control.schemas import SchemaProductBase

@pytest.mark.asyncio
async def test_get_content(pokeapi_api_provider):
    """
    Test if the API returns the correct number of Pokemon.
    """
    await pokeapi_api_provider.get_content(50)

    assert pokeapi_api_provider.results is not None
    assert len(pokeapi_api_provider.results) > 0
    assert len(pokeapi_api_provider.results) == 50

@pytest.mark.asyncio
async def test_standardize_content(pokeapi_content_provider, pokeapi_api_provider):
    """
    Test if the content is properly standardized to SchemaProductBase format.
    """
    pokeapi_content_provider
    data = await pokeapi_api_provider.standardize_content(50)

    assert isinstance(data, list)
    assert all(isinstance(item, SchemaProductBase) for item in data)
    assert len(data) == 50

    # Validate first item structure
    first_item = data[0]
    assert isinstance(first_item.ext_id, str)
    assert isinstance(first_item.name, str)
    assert isinstance(first_item.value, (int, float))
    assert isinstance(first_item.description, str)
    assert first_item.image is not None

@pytest.mark.asyncio
async def test_should_handle_api_errors(pokeapi_api_provider):
    """
    Test API error handling with invalid parameters.
    """
    with pytest.raises(ValueError, match='Limit must be positive'):
        await pokeapi_api_provider.get_content(-1)

    with pytest.raises(ValueError, match='Limit cannot exceed 100'):
        await pokeapi_api_provider.get_content(101)

@pytest.mark.asyncio
async def test_should_validate_standardized_content_structure(pokeapi_content_provider, pokeapi_api_provider):
    """Test if standardized content has all required fields with correct types"""
    pokeapi_content_provider
    data = await pokeapi_api_provider.standardize_content(1)

    product = data[0]
    assert hasattr(product, 'name')
    assert hasattr(product, 'description')
    assert hasattr(product, 'value')
    assert isinstance(product.value, (int, float))
    assert product.value > 0
    assert len(product.name) > 0
    assert len(product.description) > 0
