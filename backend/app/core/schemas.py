from pydantic import BaseModel
from typing import List, Generic, TypeVar, Optional

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response schema
    """
    total: int
    skip: int
    limit: int
    data: List[T]


class ErrorResponse(BaseModel):
    """
    Standard error response schema
    """
    detail: str
    error_code: Optional[str] = None