"""Authentication and Role-Based Access Control (RBAC) ORM Models."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base, TimestampMixin, UUIDMixin

# Association table for User <-> Role (Many-to-Many)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for Role <-> Permission (Many-to-Many)
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base, UUIDMixin, TimestampMixin):
    """User account model supporting citizens, analysts, officers, and administrators."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    state_of_residence: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship("Role", secondary=user_roles, back_populates="users", lazy="selectin")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="submitter")
    verifications: Mapped[List["VerificationRecord"]] = relationship("VerificationRecord", back_populates="verified_by_user")
    alerts_created: Mapped[List["Alert"]] = relationship("Alert", back_populates="created_by_user", foreign_keys="Alert.created_by_user_id")
    notification_preferences: Mapped[Optional["NotificationPreference"]] = relationship("NotificationPreference", back_populates="user", uselist=False)

    def has_role(self, role_name: str) -> bool:
        """Check if user possesses a specific role."""
        return any(role.name.upper() == role_name.upper() for role in self.roles)

    def has_permission(self, permission_slug: str) -> bool:
        """Check if user possesses a specific permission through any of their roles."""
        for role in self.roles:
            if any(perm.slug == permission_slug for perm in role.permissions):
                return True
        return False


class Role(Base, UUIDMixin, TimestampMixin):
    """RBAC Role entity (e.g. CITIZEN, ANALYST, VERIFICATION_OFFICER, SECURITY_OFFICER, ADMINISTRATOR)."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", secondary=user_roles, back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="selectin")


class Permission(Base, UUIDMixin, TimestampMixin):
    """Fine-grained permission slug (e.g. reports:view_all, claims:verify)."""

    __tablename__ = "permissions"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    roles: Mapped[List["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")
