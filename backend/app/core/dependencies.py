"""FastAPI route dependencies for authentication, authorization, and database sessions."""

from typing import Callable, Optional
from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import decode_token, is_token_revoked
from backend.app.core.exceptions import AuthenticationException, AuthorizationException
from backend.app.modules.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT access token and return the active User entity."""
    if not token:
        raise AuthenticationException("Authentication required. Missing Bearer token.")

    payload = decode_token(token, expected_type="access")

    # Check token revocation
    if is_token_revoked(db, token):
        raise AuthenticationException("Authentication token has been revoked. Please log in again.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Malformed authentication token.")

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise AuthenticationException("User account associated with this token no longer exists.")

    if not user.is_active:
        raise AuthorizationException("User account has been deactivated.")

    # Check for active account lockout
    if user.locked_until:
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if locked_until > now:
            remaining_seconds = int((locked_until - now).total_seconds())
            raise AuthorizationException(
                f"Account is temporarily locked due to repeated failed login attempts. Retry in {remaining_seconds}s."
            )

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Retrieve user if valid Bearer token provided, otherwise return None (for anonymous citizen actions)."""
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except (AuthenticationException, AuthorizationException):
        return None


def require_role(required_role: str) -> Callable[[User], User]:
    """Factory dependency requiring the user to have a specific role."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_role(required_role) and not current_user.has_role("ADMINISTRATOR"):
            raise AuthorizationException(
                f"Operation requires '{required_role}' role. Current user does not possess this authorization."
            )
        return current_user

    return role_checker


def require_permission(required_permission: str) -> Callable[[User], User]:
    """Factory dependency requiring the user to possess a specific fine-grained permission."""

    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(required_permission) and not current_user.has_role("ADMINISTRATOR"):
            raise AuthorizationException(
                f"Permission '{required_permission}' is required to perform this action."
            )
        return current_user

    return permission_checker


def require_any_permission(*required_permissions: str) -> Callable[[User], User]:
    """Factory dependency requiring the user to possess at least one of the specified permissions."""

    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.has_role("ADMINISTRATOR"):
            return current_user
        if not any(current_user.has_permission(p) for p in required_permissions):
            raise AuthorizationException(
                f"One of the following permissions is required: {', '.join(required_permissions)}"
            )
        return current_user

    return permission_checker
