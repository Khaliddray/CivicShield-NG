"""Authentication business logic service."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    compute_audit_hash,
)
from backend.app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    DuplicateEntityException,
    EntityNotFoundException,
)
from backend.app.modules.security_audit.service import SecurityAuditService
from backend.app.modules.auth.models import User, Role
from backend.app.modules.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserOut,
)
from backend.app.modules.notifications.models import NotificationPreference
from backend.app.modules.security_audit.models import AuditLog, SecurityEvent
from backend.app.common.enums import UserRoleType, SecurityEventType, PriorityLevel


class AuthService:
    """Manages user authentication lifecycle, token distribution, and security events."""

    @staticmethod
    def register_user(
        db: Session,
        request: UserRegisterRequest,
        role_name: str = UserRoleType.CITIZEN.value,
        ip_address: Optional[str] = None,
    ) -> User:
        """Register a new user account with secure defaults and default role."""
        # 1. Check for email collision
        existing = db.execute(select(User).where(User.email == request.email.lower())).scalar_one_or_none()
        if existing:
            raise DuplicateEntityException("User", "email", request.email)

        # 2. Retrieve requested role
        role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
        if not role:
            raise EntityNotFoundException("Role", role_name)

        # 3. Create user entity
        user = User(
            email=request.email.lower(),
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            phone_number=request.phone_number,
            state_of_residence=request.state_of_residence,
            is_active=True,
            is_verified=False,
        )
        user.roles.append(role)
        db.add(user)
        db.flush()

        # 4. Provision default notification preferences
        pref = NotificationPreference(
            user_id=user.id,
            preferred_states=[request.state_of_residence] if request.state_of_residence else [],
            receive_critical_alerts=True,
            receive_high_alerts=True,
            receive_medium_alerts=True,
            channel_in_app=True,
        )
        db.add(pref)

        # 5. Record audit log
        SecurityAuditService.record_audit(
            db=db,
            action="USER_REGISTER",
            entity_type="USER",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            details={"email": user.email, "role": role_name},
            commit=False,
        )

        db.commit()
        db.refresh(user)
        logger.info(f"Registered new user '{user.email}' with role '{role_name}'")
        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        request: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """Authenticate user credentials, enforce rate-limit lockout, and issue JWT tokens."""
        user = db.execute(select(User).where(User.email == request.email.lower())).scalar_one_or_none()

        if not user:
            # Constant-time mitigation against timing attacks
            hash_password("dummy-timing-defense-password")
            AuthService._record_security_event(
                db, SecurityEventType.AUTH_FAILURE.value, PriorityLevel.LOW.value,
                ip_address, request.email, {"reason": "Non-existent user"}
            )
            db.commit()
            raise AuthenticationException("Invalid email or password.")

        # Check account lockout
        now = datetime.now(timezone.utc)
        if user.locked_until:
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > now:
                seconds_left = int((locked_until - now).total_seconds())
                raise AuthorizationException(f"Account locked due to repeated failed logins. Try again in {seconds_left} seconds.")

        # Verify password
        if not verify_password(request.password, user.password_hash):
            user.failed_login_attempts += 1
            severity = PriorityLevel.LOW.value
            event_type = SecurityEventType.AUTH_FAILURE.value

            if user.failed_login_attempts >= settings.RATE_LIMIT_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.RATE_LIMIT_LOCKOUT_MINUTES)
                severity = PriorityLevel.HIGH.value
                event_type = SecurityEventType.BRUTE_FORCE_SUSPECTED.value
                logger.warning(f"Account '{user.email}' locked until {user.locked_until} due to failed login attempts.")

            AuthService._record_security_event(
                db, event_type, severity, ip_address, user.email,
                {"failed_attempts": user.failed_login_attempts, "locked": user.locked_until is not None}
            )
            db.commit()
            raise AuthenticationException("Invalid email or password.")

        if not user.is_active:
            raise AuthorizationException("Account has been deactivated. Please contact support.")

        # Reset failed login counter on success
        user.failed_login_attempts = 0
        user.locked_until = None

        # Issue tokens
        role_names = [r.name for r in user.roles]
        additional_claims = {"roles": role_names, "email": user.email}
        access_token = create_access_token(subject=user.id, additional_claims=additional_claims)
        refresh_token = create_refresh_token(subject=user.id)

        # Audit login
        SecurityAuditService.record_audit(
            db=db,
            action="USER_LOGIN",
            entity_type="USER",
            entity_id=user.id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": user.email, "roles": role_names},
            commit=False,
        )
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )

    @staticmethod
    def refresh_access_token(db: Session, refresh_token_str: str) -> TokenResponse:
        """Validate refresh token and issue a fresh token pair."""
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id = payload.get("sub")

        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user or not user.is_active:
            raise AuthenticationException("Invalid or inactive user account.")

        role_names = [r.name for r in user.roles]
        additional_claims = {"roles": role_names, "email": user.email}
        new_access_token = create_access_token(subject=user.id, additional_claims=additional_claims)
        new_refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserOut.model_validate(user),
        )

    @staticmethod
    def _record_security_event(
        db: Session,
        event_type: str,
        severity: str,
        ip_address: Optional[str],
        user_identifier: Optional[str],
        details: dict,
    ) -> None:
        """Helper to log security incidents."""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            ip_address=ip_address,
            user_identifier=user_identifier,
            details=details,
        )
        db.add(event)
