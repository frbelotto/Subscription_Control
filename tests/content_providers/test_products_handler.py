import pytest

from subscription_control.content_providers.content_providers import create_content_provider, list_content_provider
from subscription_control.logger import logger
from subscription_control.schemas import SchemaContentProviderBase, SchemaProductBase
from subscription_control.content_providers.products_handler import update_products, remove_products, list_products

@pytest.fixture
def valid_content_provider():
    return SchemaContentProviderBase(
        name='test_provider',
        description='test description',
        api_engine_module_name='pokeapi.py',
        email='test@example.com',
    )

@pytest.mark.asyncio
async def test_update_products_all_providers(valid_content_provider):
    """Test updating products from all content providers"""
    await create_content_provider(valid_content_provider)

    content_providers = await list_content_provider()
    if content_providers is None or not content_providers:
        logger.error(f'Content provider list is None or empty : {content_providers}')
        raise ValueError('Content provider list is None or empty')

    logger.info(f'Available content_providers are : {content_providers}')

    products = await update_products(limit=5)
    if products is None or not products:
        logger.error(f'Products list is None or empty : {products}')
        raise ValueError('Products list is None or empty')
    logger.info(f'Products: {products}')
    assert len(products) > 0
    # Check for specific fields in the products
    for product in products:
        assert hasattr(product, 'name')
        assert hasattr(product, 'description')
        assert hasattr(product, 'value')
        assert hasattr(product, 'image')

@pytest.mark.asyncio
async def test_remove_products_all(valid_content_provider):
    """Test removing all products"""
    # Include products for removing
    await create_content_provider(valid_content_provider)
    await update_products(limit=5)
    product_list = await list_products()
    logger.info(f'List of products: {product_list}')
    
    removed_count = await remove_products()
    logger.info(f'Removed : {removed_count}')
    assert isinstance(removed_count, int)

# Novos testes adicionados

@pytest.mark.asyncio
async def test_update_products_specific_provider(valid_content_provider):
    """Test updating products from a specific content provider"""
    created_provider = await create_content_provider(valid_content_provider)
    
    # Atualizar produtos apenas do provedor específico
    products = await update_products(content_provider_id=created_provider.id, limit=3)
    assert len(products) > 0
    
    # Verificar se todos os produtos pertencem ao provedor especificado
    for product in products:
        assert product.content_provider_id == created_provider.id

@pytest.mark.asyncio
async def test_remove_products_specific_provider(valid_content_provider):
    """Test removing products from a specific content provider"""
    # Criar dois provedores e produtos para ambos
    provider1 = await create_content_provider(valid_content_provider)
    
    provider2 = await create_content_provider(SchemaContentProviderBase(
        name='second_provider',
        description='another test provider',
        api_engine_module_name='tmdb.py',
        email='second@test.com',
    ))
    
    # Adicionar produtos para ambos os provedores
    await update_products(content_provider_id=provider1.id, limit=3)
    await update_products(content_provider_id=provider2.id, limit=3)
    
    # Verificar que produtos existem para ambos os provedores
    all_products_before = await list_products()
    assert len(all_products_before) >= 6
    
    # Remover apenas os produtos do primeiro provedor
    removed_count = await remove_products(content_provider_id=provider1.id)
    assert removed_count > 0
    
    # Verificar que os produtos do primeiro provedor foram removidos
    products_provider1 = await list_products(content_provider_id=provider1.id)
    assert len(products_provider1) == 0
    
    # Verificar que os produtos do segundo provedor ainda existem
    products_provider2 = await list_products(content_provider_id=provider2.id)
    assert len(products_provider2) > 0

@pytest.mark.asyncio
async def test_list_products_filtering(valid_content_provider):
    """Test listing products with filtering"""
    # Limpar produtos existentes
    await remove_products()
    
    # Criar produtos para um provedor específico
    provider = await create_content_provider(valid_content_provider)
    await update_products(content_provider_id=provider.id, limit=5)
    
    # Listar todos os produtos
    all_products = await list_products()
    assert len(all_products) >= 5
    
    # Listar produtos apenas deste provedor
    filtered_products = await list_products(content_provider_id=provider.id)
    assert len(filtered_products) >= 5
    
    # Verificar que todos os produtos filtrados pertencem ao provedor correto
    for product in filtered_products:
        assert product.content_provider_id == provider.id

@pytest.mark.asyncio
async def test_update_products_empty_result():
    """Test updating products for a non-existent content provider"""
    # Tentar atualizar produtos para um ID de provedor que não existe
    with pytest.raises(ValueError, match='No content provider found with the given ID'):
        await update_products(content_provider_id=999999)

@pytest.mark.asyncio
async def test_remove_products_no_products():
    """Test removing products when there are no products"""
    # Primeiro remover todos os produtos
    await remove_products()
    
    # Tentar remover novamente - deve retornar 0
    removed_count = await remove_products()
    assert removed_count == 0
