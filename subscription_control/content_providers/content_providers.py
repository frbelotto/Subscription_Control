from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, ValidationError, validate_call
from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError

from subscription_control.database import get_session
from subscription_control.logger import logger
from subscription_control.models import ContentProvider
from subscription_control.schemas import SchemaContentProvider, SchemaContentProviderBase


@validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=True))
async def create_content_provider(content: SchemaContentProviderBase) -> SchemaContentProvider | Dict[str, Any]:
    """
    Creates a new content provider.

    Parameters:
    - content (SchemaContentProviderBase): The content provider data.

    Returns:
    - SchemaContentProvider | Dict[str, Any]: The created content provider or an error dictionary.
    """
    db_content = ContentProvider(
        name=content.name,
        description=content.description if content.description is not None else '',
        email=content.email,
        api_engine_module_name=content.api_engine_module_name,
    )

    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            s.add(db_content)
            await s.commit()
            await s.refresh(db_content)
            return SchemaContentProvider.model_validate(db_content)
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
            return {'error': f'Unexpected error: {e}'}


@validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=False))
async def list_content_provider(
    id: Optional[int] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    email: Optional[str] = None, 
    api_engine_module_name: Optional[str] = None
) -> List[SchemaContentProvider] | Dict[str, Any]:
    """
    Lists content providers based on the provided filters.

    Parameters:
    - id (Optional[int]): Filter by content provider ID.
    - name (Optional[str]): Filter by content provider name.
    - description (Optional[str]): Filter by content provider description.
    - email (Optional[str]): Filter by content provider email.
    - api_engine_module_name (Optional[str]): Filter by API engine module name.

    Returns:
    - List[SchemaContentProvider] | Dict[str, Any]: List of content providers matching the filters or an error dictionary.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            filters: list[Any] = []
            if id is not None:
                filters.append(ContentProvider.id == id)
            if name:
                filters.append(func.lower(ContentProvider.name).like(f'%{name.lower()}%'))
            if description:
                filters.append(func.lower(ContentProvider.description).like(f'%{description.lower()}%'))
            if email:
                filters.append(func.lower(ContentProvider.email).like(f'%{email.lower()}%'))
            if api_engine_module_name:
                filters.append(func.lower(ContentProvider.api_engine_module_name).like(f'%{api_engine_module_name.lower()}%'))

            stmt = select(ContentProvider).where(and_(*filters)) if filters else select(ContentProvider)

            result = await s.execute(stmt)
            return [SchemaContentProvider.model_validate(row) for row in result.scalars().all()]
        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            return {'error': f'Unexpected error: {e}'}


@validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=False))
async def delete_content_provider(content_provider_id: int) -> Dict[str, Any]:
    """
    Deletes a content provider based on the provided ID.

    Parameters:
    - content_provider_id (int): ID of the content provider to be deleted.

    Returns:
    - Dict[str, Any]: Dictionary with the result of the deletion or an error message.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            # Check if content_provider_id exists
            stmt_check = select(ContentProvider).where(ContentProvider.id == content_provider_id)
            result_check = await s.execute(stmt_check)
            content_provider = result_check.scalar_one_or_none()

            if content_provider is None:
                logger.warning(f'Content provider with ID {content_provider_id} not found.')
                return {'error': 'Content provider not found'}

            # Delete content_provider_id
            stmt_delete = delete(ContentProvider).where(ContentProvider.id == content_provider_id)
            await s.execute(stmt_delete)
            await s.commit()
            logger.info(f'Content provider with ID {content_provider_id} deleted successfully.')
            return {'message': 'Content provider deleted successfully'}
        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            return {'error': f'Unexpected error: {e}'}
