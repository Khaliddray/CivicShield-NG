"""Authentication and Access Control API Endpoints."""

from typing import List, Optional
import math
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, require_permission
from backend.app.common.schemas import APIResponse, PaginatedResponse, PaginationMeta
from backend.app.modules.auth.models import User
from backend.app.modules.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserOut,
    UserUpdateRolesRequest,
    UserUpdateStatusRequest,
    LogoutResponse,
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


@router.post(
    "/logout",
    response_model=APIResponse[LogoutResponse],
    summary="Terminate active session and log out",
)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIResponse[LogoutResponse]:
    """Record session termination in the cryptographic audit ledger."""
    client_ip = request.client.host if request.client else None
    token = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    AuthService.logout_user(db=db, current_user=current_user, token=token, ip_address=client_ip)
    return APIResponse(
        data=LogoutResponse(),
        message="You have been successfully logged out.",
    )


@router.get(
    "/users",
    response_model=APIResponse[PaginatedResponse[UserOut]],
    summary="List registered users (Administrators)",
)
def list_users(
    role: Optional[str] = Query(None, description="Filter by role name (e.g. CITIZEN, ANALYST)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[UserOut]]:
    """Administrative user management endpoint."""
    skip = (page - 1) * page_size
    users, total = AuthService.list_users(
        db=db,
        role_name=role,
        is_active=is_active,
        search_query=search,
        skip=skip,
        limit=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return APIResponse(
        data=PaginatedResponse(
            items=[UserOut.model_validate(u) for u in users],
            pagination=PaginationMeta(
                total_count=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        ),
        message="Users retrieved successfully.",
    )


@router.get(
    "/users/{user_id}",
    response_model=APIResponse[UserOut],
    summary="Get user account details by ID (Administrators)",
)
def get_user_detail(
    user_id: str,
    current_user: User = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[UserOut]:
    """Inspect user profile and role details."""
    user = AuthService.get_user_by_id(db=db, user_id=user_id)
    return APIResponse(
        data=UserOut.model_validate(user),
        message="User details retrieved successfully.",
    )


@router.patch(
    "/users/{user_id}/roles",
    response_model=APIResponse[UserOut],
    summary="Update user assigned roles (Administrators)",
)
def update_user_roles(
    user_id: str,
    payload: UserUpdateRolesRequest,
    request: Request,
    current_user: User = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[UserOut]:
    """Assign or modify user roles with security audit tracking."""
    client_ip = request.client.host if request.client else None
    updated_user = AuthService.update_user_roles(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        role_names=payload.roles,
        ip_address=client_ip,
    )
    return APIResponse(
        data=UserOut.model_validate(updated_user),
        message=f"User roles updated successfully to {payload.roles}.",
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=APIResponse[UserOut],
    summary="Activate or deactivate user account (Administrators)",
)
def update_user_status(
    user_id: str,
    payload: UserUpdateStatusRequest,
    request: Request,
    current_user: User = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> APIResponse[UserOut]:
    """Toggle user active status with security audit tracking."""
    client_ip = request.client.host if request.client else None
    updated_user = AuthService.update_user_status(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        is_active=payload.is_active,
        ip_address=client_ip,
    )
    status_str = "activated" if payload.is_active else "deactivated"
    return APIResponse(
        data=UserOut.model_validate(updated_user),
        message=f"User account {status_str} successfully.",
    )
