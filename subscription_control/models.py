from datetime import datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, registry

from subscription_control.database import sync_engine

table_registry = registry()


@table_registry.mapped_as_dataclass
class ContentProvider:
    """
    SQLAlchemy model for content providers table
    """
    __tablename__ = 'content_providers'

    # Add table indexes for better performance
    __table_args__ = (
        Index('idx_content_provider_name', 'name'),
        Index('idx_content_provider_email', 'email'),
    )

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True, unique=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    api_engine_module_name: Mapped[str] = mapped_column(unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
        comment='Record creation timestamp',
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment='Record last update timestamp',
    )


@table_registry.mapped_as_dataclass
class Product:
    """
    SQLAlchemy model for products table
    """
    __tablename__ = 'products'

    __table_args__ = (
        UniqueConstraint('content_provider_id', 'ext_id', name='uq_content_provider_ext_id'),
    )
    content_provider_id: Mapped[int] = mapped_column(ForeignKey('content_providers.id'), nullable=False)
    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True, unique=True)
    ext_id: Mapped[str] = mapped_column(unique=False, nullable=False)
    name: Mapped[str] = mapped_column(unique=False, nullable=False)
    value: Mapped[int] = mapped_column(unique=False, nullable=True)
    image: Mapped[str] = mapped_column(unique=False, nullable=True)
    description: Mapped[str] = mapped_column(unique=False, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
        comment='Record creation timestamp',
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment='Record last update timestamp',
    )

@table_registry.mapped_as_dataclass
class Consumer:
    """
    SQLAlchemy model for consumer table
    """
    __tablename__ = 'consumer'

    id: Mapped[int] = mapped_column(init=False, primary_key=True, autoincrement=True, unique=True)
    name: Mapped[str] = mapped_column(unique=False, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
        comment='Record creation timestamp',
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment='Record last update timestamp',
    )

table_registry.metadata.create_all(bind=sync_engine)
