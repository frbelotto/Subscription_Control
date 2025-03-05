from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, ValidationError, validate_call
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from subscription_control.content_providers.content_provider_handler import ContentHandler
from subscription_control.content_providers.content_providers import list_content_provider
from subscription_control.database import get_session
from subscription_control.logger import logger
from subscription_control.models import Product
from subscription_control.schemas import SchemaProduct, SchemaProductBase


@validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=False))
async def update_products(content_provider_id: Optional[int] = None, limit: Optional[int] = 10) -> List[SchemaProductBase] | Any:
    """
    Updates content for the specified content provider or all content providers if no ID is provided.

    Parameters:
    - content_provider_id (Optional[int]): ID of the content provider to update. If None, updates all content providers.
    - limit (Optional[int]): Limit on the number of content items to update. Default is 10.

    Returns:
    - list[SchemaProductBase]: List of updated content items.
    """
    provider = ContentHandler()
    content: List[SchemaProductBase] = []

    try:
        if content_provider_id is None:
            logger.info(f'Configuration files of identified content providers: {provider.providers}')
            for provider_name in provider.providers.keys():
                await update_provider_content(provider, provider_name, content, limit)
        else:
            await update_specific_provider_content(provider, content_provider_id, content, limit)

        db_products = create_db_products(content)

        if not db_products:
            raise ValueError('No products to update')

        logger.info(f'Products before removal: {db_products}')
        await remove_products(content_provider_id)
        inserted_products = await insert_products_into_db(db_products)

        logger.info(f'Inserted products: {inserted_products}')
        return inserted_products
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        raise e


async def update_provider_content(provider: ContentHandler, provider_name: str, content: List[SchemaProductBase], limit: Optional[int]) -> None:
    available = await list_content_provider(api_engine_module_name=provider_name)
    if available is None or not available:
        logger.error(f'Provider configuration file is not found on providers existing list: {provider_name}')
    else:
        logger.info(f'Updating info for {provider_name}')
        content.extend(await provider.standardize_content(provider_name, limit=limit))


async def update_specific_provider_content(provider: ContentHandler, content_provider_id: int, content: List[SchemaProductBase], limit: Optional[int]) -> None:
    result = await list_content_provider(id=content_provider_id)
    if result and isinstance(result, list) and len(result) > 0:
        api_engine_module_name = result[0].api_engine_module_name.replace('.py', '') if result[0].api_engine_module_name else None
        if not api_engine_module_name:
            raise ValueError('api_engine_module_name is None')
        logger.info(f'Updating info for {api_engine_module_name}')
        content.extend(await provider.standardize_content(api_engine_module_name, limit=limit))
    else:
        raise ValueError('No content provider found with the given ID')


def create_db_products(content: List[SchemaProductBase]) -> List[Product]:
    return [
        Product(
            content_provider_id=item.content_provider_id,
            ext_id=item.ext_id,
            name=item.name,
            value=int(item.value) if item.value is not None else 0,
            image=str(item.image),
            description=item.description if item.description is not None else ''
        )
        for item in content
    ]


async def insert_products_into_db(db_products: List[Product]) -> List[SchemaProduct] | Dict[str, str]:
    """
    Inserts the given products into the database.

    Parameters:
    - db_products (list): List of products to insert into the database.

    Returns:
    - list[SchemaProduct]: List of inserted products.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            s.add_all(db_products)
            await s.commit()
            for product in db_products:
                await s.refresh(product)

            return [SchemaProduct.model_validate(product) for product in db_products]
        except IntegrityError as e:
            await s.rollback()
            logger.error(f'IntegrityError: {e}')
            raise e
        except ValidationError as e:
            await s.rollback()
            logger.error(f'ValidationError: {e}')
            return {'error': f'ValidationError: {e}'}
        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            raise e


async def remove_products(content_provider_id: Optional[int] = None) -> int:
    """
    Removes all products from the database.

    Parameters:
    - content_provider_id (Optional[int]): ID of the content provider whose products should be removed. If None, removes all products.

    Returns:
    - int: Number of products removed.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            if content_provider_id:
                products_to_delete = await s.execute(select(Product).where(Product.content_provider_id == content_provider_id))
            else:
                products_to_delete = await s.execute(select(Product))
            products_list = products_to_delete.scalars().all()
            logger.info(f'Products to delete: {products_list}')
            if not products_list:
                logger.info('No existing products found to delete')
                return 0
            if content_provider_id:
                await s.execute(delete(Product).where(Product.content_provider_id == content_provider_id))
            else:
                await s.execute(delete(Product))
            await s.commit()
            logger.info(f'Number of products deleted: {len(products_list)}')
            return len(products_list)
        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            raise e


async def list_products(content_provider_id: Optional[int] = None) -> List[SchemaProduct]:
    """
    Lists all products from the database.

    Parameters:
    - content_provider_id (Optional[int]): ID of the content provider whose products should be listed. If None, lists all products.

    Returns:
    - list[SchemaProduct]: List of products.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            stmt = select(Product).where(Product.content_provider_id == content_provider_id) if content_provider_id else select(Product)
            result = await s.execute(stmt)

            if not result:
                return []
            
            return [SchemaProduct.model_validate(row) for row in result.scalars().all()]

        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            raise e
