"""Generic API response models and pagination wrappers."""

from typing import Generic, List, Optional, TypeVar
from datetime import datetime, timezone
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standardized top-level API envelope."""

    success: bool = True
    data: Optional[DataT] = None
    message: str = "Operation completed successfully."
    errors: Optional[List[dict]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaginationMeta(BaseModel):
    """Metadata for paginated queries."""

    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated collection envelope."""

    items: List[DataT]
    pagination: PaginationMeta
