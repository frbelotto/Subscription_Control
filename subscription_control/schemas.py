from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field

myclassconfig = {
    'str_strip_whitespace': True,
    'str_to_lower': True,
    'validate_default': True,
    'validate_assignment': True,
    'extra': 'forbid',
}

class SchemaContentProviderBase(BaseModel):
    """
    Base schema for content provider information

    Attributes:
        name: Provider name
        description: Optional provider description
        email: Provider contact email
        api_engine_module_name: Name of the API engine module
    """
    model_config = ConfigDict(**myclassconfig)
    name: str
    description: Optional[str] = None
    email: EmailStr
    api_engine_module_name: str

class SchemaContentProvider(SchemaContentProviderBase):
    """
    Complete schema for content provider with database fields
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

class SchemaProductBase(BaseModel):
    """
    Base schema for product information
    """
    model_config = ConfigDict(**myclassconfig)
    content_provider_id: int
    ext_id: str
    name: str
    value: float | None
    image: HttpUrl | None
    description: str | None

class SchemaProduct(SchemaProductBase):
    """
    Complete schema for product with database fields
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

class ContentProviderSystem(ABC):
    """
    Abstract base class defining the interface for content provider systems
    """
    @abstractmethod
    def get_content(self, endpoint: str) -> None:
        pass

    @abstractmethod
    def standardize_content(self, content: list[dict]) -> list[SchemaProductBase]:
        pass
