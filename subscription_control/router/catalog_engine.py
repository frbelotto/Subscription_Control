import logging
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from subscription_control.content_providers.content_providers import (
    create_content_provider,
    delete_content_provider,
    list_content_provider,
)
from subscription_control.schemas import (
    SchemaContentProvider,
    SchemaContentProviderBase,
    SchemaProductBase,
    SchemaProduct,
)
from subscription_control.content_providers.products_handler import update_products, remove_products, list_products

logger = logging.getLogger(__name__)

content_providers_router = APIRouter(prefix='/content_provider', tags=['content_providers'])

@content_providers_router.post('/', status_code=HTTPStatus.CREATED, response_model=SchemaContentProvider, responses={400: {'model': dict}, 500: {'model': dict}})
async def input_content_provider(content: SchemaContentProviderBase) -> SchemaContentProvider:
    """
    Create a new content provider.

    Args:
        content (SchemaContentProviderBase): The content provider data.

    Returns:
        SchemaContentProvider: The created content provider.

    Raises:
        HTTPException: If there's a database conflict or other error.
    """
    try:
        return await create_content_provider(content)
    except IntegrityError as e:
        logger.error(f'Database integrity error: {e}')
        error_detail = {
            'error': 'IntegrityError',
            'message': 'A content provider with these details already exists',
            'details': str(e.orig),
        }
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=error_detail)
    except Exception:
        logger.exception('Unexpected error while creating content provider')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail='An unexpected error occurred')

@content_providers_router.get('/', status_code=HTTPStatus.OK, response_model=list[SchemaContentProvider] | dict, responses={200: {'model': list[SchemaContentProvider]}, 400: {'model': dict}, 500: {'model': dict}})
async def show_content_providers(id: int | None = None, name: str | None = None, description: str | None = None, email: str | None = None, api_engine_module_name: str | None = None) -> list[SchemaContentProvider] | dict:
    """
    Retrieve content providers with optional filtering.

    Args:
        id: Optional filter by provider ID
        name: Optional filter by provider name
        description: Optional filter by description
        email: Optional filter by email
        api_engine_module_name: Optional filter by API engine module name

    Returns:
        List of content providers matching the filters or error dictionary
    """
    try:
        result = await list_content_provider(
            id=id,
            name=name,
            description=description,
            email=email,
            api_engine_module_name=api_engine_module_name
        )

        if isinstance(result, dict) and 'error' in result:
            logger.error(f'Error retrieving content providers: {result["error"]}')
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=result['error'])

        return result

    except Exception as e:
        logger.exception('Unexpected error while retrieving content providers')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {str(e)}')

@content_providers_router.delete('/', status_code=HTTPStatus.NO_CONTENT, responses={204: {'description': 'Content provider deleted successfully'}, 400: {'model': dict}, 404: {'model': dict}, 500: {'model': dict}})
async def delete_content_provider_route(content_provider_id: Optional[int] = None) -> None:
    """
    Delete a content provider by ID.

    Args:
        content_provider_id (Optional[int]): The ID of the content provider to delete.

    Raises:
        HTTPException: If the content provider is not found or there's an error.
    """
    if content_provider_id is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Content provider ID must be provided')
    try:
        result = await delete_content_provider(content_provider_id)

        if 'error' in result:
            if result['error'] == 'Content provider not found':
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=result['error'])

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception('Unexpected error while deleting content provider')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {str(e)}')

product_handler_router = APIRouter(prefix='/product_handler', tags=['product_handler'])

@product_handler_router.post('/update_products', status_code=HTTPStatus.OK, response_model=List[SchemaProductBase] | dict, responses={200: {'model': List[SchemaProductBase]}, 500: {'model': dict}})
async def start_update_products(content_provider_id: Optional[int] = None, limit: Optional[int] = 10) -> List[SchemaProductBase] | dict:
    """
    Start the update process for products.

    Args:
        content_provider_id (Optional[int]): ID of the content provider to update. If None, updates all content providers.
        limit (Optional[int]): Limit on the number of content items to update. Default is 10.

    Returns:
        List[SchemaProductBase] | dict: List of updated content items or error dictionary.
    """
    try:
        return await update_products(content_provider_id, limit)
    except Exception as e:
        logger.exception('Unexpected error while updating products')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {str(e)}')

@product_handler_router.delete('/remove_products', status_code=HTTPStatus.NO_CONTENT, responses={204: {'description': 'Products removed successfully'}, 500: {'model': dict}})
async def start_remove_products(content_provider_id: Optional[int] = None) -> None:
    """
    Remove products from the database.

    Args:
        content_provider_id (Optional[int]): ID of the content provider whose products should be removed. If None, removes all products.

    Raises:
        HTTPException: If there's an error during the removal process.
    """
    try:
        await remove_products(content_provider_id)
    except Exception as e:
        logger.exception('Unexpected error while removing products')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {str(e)}')

@product_handler_router.get('/list_products', status_code=HTTPStatus.OK, response_model=List[SchemaProduct] | dict, responses={200: {'model': List[SchemaProduct]}, 500: {'model': dict}})
async def start_list_products(content_provider_id: Optional[int] = None) -> List[SchemaProduct] | dict:
    """
    List products from the database.

    Args:
        content_provider_id (Optional[int]): ID of the content provider whose products should be listed. If None, lists all products.

    Returns:
        List[SchemaProduct] | dict: List of products or error dictionary.
    """
    try:
        return await list_products(content_provider_id)
    except Exception as e:
        logger.exception('Unexpected error while listing products')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f'An unexpected error occurred: {str(e)}')


