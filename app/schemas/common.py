"""Standard API response envelope."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: T | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    data: dict[str, Any] | None = None


class PaginatedMeta(BaseModel):
    total: int
    page: int = 1
    page_size: int = 20


class HealthData(BaseModel):
    status: str = "healthy"
    app: str
    version: str
    database: str
    redis: str


def success_response(data: Any = None, message: str = "Operation successful") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def error_response(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "message": message, "data": data}
