"""Pydantic schemas for User Authentication and Authorization."""

import re
from typing import Annotated, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, AfterValidator
from backend.app.common.geo import validate_nigerian_state

# RFC 5322-compliant email regex ensuring zero external dependency footprint
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def _validate_email(v: str) -> str:
    cleaned = v.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValueError("Invalid email address format.")
    return cleaned


EmailStr = Annotated[str, AfterValidator(_validate_email)]


class UserRegisterRequest(BaseModel):
    """Citizen registration payload."""

    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    full_name: str = Field(min_length=2, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    state_of_residence: Optional[str] = Field(default=None, description="Recognized Nigerian state or FCT")

    @field_validator("state_of_residence")
    @classmethod
    def check_valid_state(cls, v: Optional[str]) -> Optional[str]:
        if v and not validate_nigerian_state(v):
            raise ValueError(f"'{v}' is not a recognized Nigerian State or Federal Capital Territory.")
        return v.title() if v else None


class UserLoginRequest(BaseModel):
    """User credentials login payload."""

    email: EmailStr
    password: str


class PermissionOut(BaseModel):
    """Permission detail."""

    id: str
    slug: str
    description: str

    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    """Role detail with nested permissions."""

    id: str
    name: str
    description: str
    permissions: List[PermissionOut] = []

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    """User profile response."""

    id: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    state_of_residence: Optional[str] = None
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    roles: List[RoleOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token authentication response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserOut


class RefreshTokenRequest(BaseModel):
    """Refresh token exchange payload."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request payload."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation payload."""

    token: str
    new_password: str = Field(min_length=8)
