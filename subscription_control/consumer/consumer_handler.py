from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, ValidationError, validate_call
from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError

from subscription_control.database import get_session
from subscription_control.logger import logger
from subscription_control.models import Consumer
from subscription_control.schemas import SchemaConsumer


@validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=False))
async def create_User(content: SchemaConsumer) -> Consumer | Dict[str, Any]:
    """
    Creates a new consumer profile.

    Parameters:
    - content (SchemaConsumer): The consumer data.

    Returns:
    - SchemaConsumer | Dict[str, Any]: The created content provider or an error dictionary.
    """
    db_content = Consumer(
        name=content.name,
        email=content.email,
        )

    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            s.add(db_content)
            await s.commit()
            await s.refresh(db_content)
            return db_content
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
async def list_consumer(
    id: Optional[int] = None,
    name: Optional[str] = None,
    email: Optional[str] = None, 
) -> List[Consumer] | Dict[str, Any]:
    """
    Lists consumer data based on the provided filters.

    Parameters:
    - id (Optional[int]): Filter by consumer ID.
    - name (Optional[str]): Filter by consumer  name.
    - email (Optional[str]): Filter by consumer email.

    Returns:
    - List[Consumer] | Dict[str, Any]: List of consumer matching the filters or an error dictionary.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            filters: list[Any] = []
            if id is not None:
                filters.append(Consumer.id == id)
            if name:
                filters.append(func.lower(Consumer.name).like(f'%{name.lower()}%'))
            if email:
                filters.append(func.lower(Consumer.email).like(f'%{email.lower()}%'))

            stmt = select(Consumer).where(and_(*filters)) if filters else select(Consumer)

            result = await s.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            return {'error': f'Unexpected error: {e}'}
        

@validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=False))
async def delete_consumer(consumer_id: int) -> Dict[str, Any]:
    """
    Deletes a consumer based on the provided ID.

    Parameters:
    - consumer_id (int): ID of the consumer to be deleted.

    Returns:
    - Dict[str, Any]: Dictionary with the result of the deletion or an error message.
    """
    async with get_session(async_mode=True) as s:  # type: ignore
        try:
            # Check if content_provider_id exists
            stmt_check = select(Consumer).where(Consumer.id == consumer_id)
            result_check = await s.execute(stmt_check)
            consumer = result_check.scalar_one_or_none()

            if consumer is None:
                logger.warning(f'Consumer with ID {consumer_id} not found.')
                return {'error': 'Consumer not found'}

            # Delete content_provider_id
            stmt_delete = delete(Consumer).where(Consumer.id == consumer_id)
            await s.execute(stmt_delete)
            await s.commit()
            logger.info(f'Consumer with ID {consumer_id} deleted successfully.')
            return {'message': 'Consumer deleted successfully'}
        except Exception as e:
            await s.rollback()
            logger.error(f'Unexpected error: {e}')
            return {'error': f'Unexpected error: {e}'}