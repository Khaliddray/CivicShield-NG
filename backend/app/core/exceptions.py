"""Standard domain exceptions and exception handlers for CivicShield NG."""

from typing import Any, Dict, List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone


class CivicShieldException(Exception):
    """Base exception for all CivicShield domain errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class EntityNotFoundException(CivicShieldException):
    """Raised when a requested resource is not found."""

    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AuthenticationException(CivicShieldException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid credentials or authentication token."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationException(CivicShieldException):
    """Raised when a user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions to perform this operation."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationException(CivicShieldException):
    """Raised when input fails domain or cryptographic validation."""

    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors,
        )


class IntegrityVerificationException(CivicShieldException):
    """Raised when a cryptographic hash or document signature fails verification."""

    def __init__(self, message: str = "Cryptographic integrity verification failed."):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class DuplicateEntityException(CivicShieldException):
    """Raised when attempting to create an already existing unique resource."""

    def __init__(self, entity_name: str, field_name: str, value: Any):
        super().__init__(
            message=f"{entity_name} with {field_name} '{value}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitExceededException(CivicShieldException):
    """Raised when a client exceeds allowed request frequency."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def civicshield_exception_handler(
    request: Request, exc: CivicShieldException
) -> JSONResponse:
    """Standardized handler for domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.message,
            "errors": exc.errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled server errors to prevent stack trace leaks."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "message": "An unexpected internal server error occurred.",
            "errors": [str(exc)] if request.app.debug else [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
