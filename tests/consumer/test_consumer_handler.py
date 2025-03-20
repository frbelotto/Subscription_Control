import pytest

from subscription_control.consumer.consumer_handler import create_User, delete_consumer, list_consumer
from subscription_control.schemas import SchemaConsumer
from subscription_control.models import Consumer


@pytest.fixture
def valid_consumer():
    return SchemaConsumer(
        name='test_consumer',
        email='test@example.com',
    )


@pytest.mark.asyncio
async def test_create_consumer(valid_consumer):
    """
    Test creating a consumer.
    """
    consumer = valid_consumer
    result = await create_User(consumer)
    assert isinstance(result, Consumer)
    assert result.name == consumer.name
    assert result.email == consumer.email


@pytest.mark.asyncio
async def test_create_consumer_duplicate(): # Verificar porque este teste está falhando
    """
    Test creating a duplicate consumer with the same email.
    """
    consumer = SchemaConsumer(
        name='Duplicate Consumer',
        email='duplicate@example.com',
    )
    from sqlalchemy.exc import IntegrityError
    from subscription_control.logger import logger

    await create_User(consumer)
    logger.info(await list_consumer()   )
    try:
        await create_User(consumer)
    except IntegrityError as e:
        assert isinstance(e, IntegrityError)
    else:
        assert False, 'IntegrityError not raised'


@pytest.mark.asyncio
async def test_list_consumers():
    """
    Test listing consumers.
    """
    consumer1 = SchemaConsumer(
        name='Consumer One',
        email='consumer1@example.com',
    )
    consumer2 = SchemaConsumer(
        name='Consumer Two',
        email='consumer2@example.com',
    )
    await create_User(consumer1)
    await create_User(consumer2)
    result = await list_consumer()
    assert isinstance(result, list)
    assert len(result) >= 2  # Using >= to be more resilient
    
    # Check for specific fields in the consumers
    for consumer in result:
        assert hasattr(consumer, 'name')
        assert hasattr(consumer, 'email')
        assert hasattr(consumer, 'id')


@pytest.mark.asyncio
async def test_list_consumers_with_filters():
    """
    Test listing consumers with filters.
    """
    consumer1 = SchemaConsumer(
        name='FilterTest',
        email='filter_test@example.com',
    )
    consumer2 = SchemaConsumer(
        name='OtherConsumer',
        email='other@example.com',
    )
    await create_User(consumer1)
    await create_User(consumer2)
    
    # Test filter by name
    result = await list_consumer(name='FilterTest')
    assert isinstance(result, list)
    assert len(result) >= 1
    assert any(consumer.name.lower() == 'filtertest' for consumer in result)
    
    # Test filter by email
    result = await list_consumer(email='filter_test@example.com')
    assert isinstance(result, list)
    assert len(result) >= 1
    assert any(consumer.email.lower() == 'filter_test@example.com' for consumer in result)


@pytest.mark.asyncio
async def test_should_filter_consumers_case_insensitive(valid_consumer: SchemaConsumer):
    """
    Test case-insensitive filtering of consumers.
    """
    await create_User(valid_consumer)
    
    # Test case-insensitive name filtering
    result = await list_consumer(name='TEST_CONSUMER')
    assert len(result) >= 1
    assert any(consumer.name.lower() == valid_consumer.name.lower() for consumer in result)
    
    # Test case-insensitive email filtering
    result = await list_consumer(email='TEST@EXAMPLE.COM')
    assert len(result) >= 1
    assert any(consumer.email.lower() == valid_consumer.email.lower() for consumer in result)


@pytest.mark.asyncio
async def test_delete_consumer(valid_consumer):
    """
    Test deleting a consumer.
    """
    created_consumer = await create_User(valid_consumer)
    result = await delete_consumer(created_consumer.id)
    assert result == {'message': 'Consumer deleted successfully'}
    
    # Verify the consumer is deleted
    all_consumers = await list_consumer(name=valid_consumer.name)
    assert not any(c.id == created_consumer.id for c in all_consumers)


@pytest.mark.asyncio
async def test_delete_consumer_not_found():
    """
    Test deleting a non-existent consumer.
    """
    result = await delete_consumer(999999)  # Using a high ID that is unlikely to exist
    assert result == {'error': 'Consumer not found'}


@pytest.mark.asyncio
async def test_list_consumer_empty_result():
    """
    Test listing consumers with filters that should return an empty list.
    """
    result = await list_consumer(name='ThisConsumerShouldNotExist12345')
    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_create_consumer_input_validation():
    """
    Test input validation when creating consumers.
    """
    from pydantic import ValidationError
    
    # Test with invalid email
    with pytest.raises(ValidationError):
        invalid_consumer = SchemaConsumer(
            name='InvalidEmail',
            email='not-an-email',  # This should cause validation error
        )


@pytest.mark.asyncio
async def test_create_consumer_whitespace_handling():
    """
    Test that whitespace is handled correctly in consumer data.
    """
    consumer = SchemaConsumer(
        name='  Whitespace  Test  ',  # Extra spaces should be stripped
        email='whitespace@test.com',
    )
    
    result = await create_User(consumer)
    assert result.name == 'whitespace  test'  # Should be stripped and lowercased
    

@pytest.mark.asyncio
async def test_list_consumers_by_id():
    """
    Test listing consumers by ID.
    """
    # Create a consumer and get its ID
    consumer = SchemaConsumer(
        name='IdTest',
        email='id_test@example.com',
    )
    created = await create_User(consumer)
    
    # Retrieve by ID
    result = await list_consumer(id=created.id)
    assert len(result) == 1
    assert result[0].id == created.id
    assert result[0].name == created.name.lower()


@pytest.mark.asyncio
async def test_list_consumers_multiple_filters():
    """
    Test listing consumers with multiple filters simultaneously.
    """
    # Create unique test consumer
    consumer = SchemaConsumer(
        name='MultiFilterTest',
        email='multi@filter.com',
    )
    await create_User(consumer)
    
    # Test with multiple filters that should match
    result = await list_consumer(
        name='multifilter',
        email='multi@filter.com'
    )
    assert len(result) >= 1
    assert all(c.name.lower() == 'multifiltertest' for c in result)
    
    # Test with filters that shouldn't match anything
    result = await list_consumer(
        name='multifilter',
        email='nonexistent@email.com'
    )
    assert len(result) == 0