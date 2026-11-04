"""Authentication and Access Control API Endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserOut,
)
from backend.app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post(
    "/register",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new citizen account",
)
def register(
    request_data: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[UserOut]:
    """Citizen self-registration endpoint."""
    client_ip = request.client.host if request.client else None
    user = AuthService.register_user(db=db, request=request_data, ip_address=client_ip)
    return APIResponse(
        data=UserOut.model_validate(user),
        message="Account registered successfully. You can now log in.",
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate and obtain JWT token pair",
)
def login(
    login_data: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """User credentials authentication endpoint."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    tokens = AuthService.authenticate_user(
        db=db,
        request=login_data,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return APIResponse(
        data=tokens,
        message="Authentication successful.",
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Refresh an expired access token",
)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Exchange a valid refresh token for a fresh token pair."""
    tokens = AuthService.refresh_access_token(db=db, refresh_token_str=refresh_data.refresh_token)
    return APIResponse(
        data=tokens,
        message="Token refreshed successfully.",
    )


@router.get(
    "/me",
    response_model=APIResponse[UserOut],
    summary="Retrieve current authenticated user profile and permissions",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserOut]:
    """Inspect active session profile, assigned roles, and granted permissions."""
    return APIResponse(
        data=UserOut.model_validate(current_user),
        message="User profile retrieved successfully.",
    )
