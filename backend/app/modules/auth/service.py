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
    def logout_user(db: Session, current_user: User, token: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """Record explicit user logout in immutable audit trail and blacklist token."""
        if token:
            from backend.app.core.security import revoke_token
            revoke_token(db=db, token=token, user_id=current_user.id, reason="USER_LOGOUT")

        SecurityAuditService.record_audit(
            db=db,
            action="USER_LOGOUT",
            entity_type="USER",
            entity_id=current_user.id,
            user_id=current_user.id,
            ip_address=ip_address,
            details={"email": current_user.email},
            commit=True,
        )
        logger.info(f"User {current_user.email} logged out successfully. Token revoked.")

    @staticmethod
    def list_users(
        db: Session,
        role_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[User], int]:
        """Administrative query to list registered users with role and status filters."""
        from sqlalchemy import func
        query = select(User)

        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if role_name:
            query = query.where(User.roles.any(Role.name == role_name.upper()))
        if search_query:
            query = query.where(
                User.email.ilike(f"%{search_query}%") | User.full_name.ilike(f"%{search_query}%")
            )

        total_count = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
        users = list(
            db.execute(query.order_by(User.created_at.desc()).offset(skip).limit(limit)).scalars().all()
        )
        return users, total_count

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Fetch user by primary key or raise EntityNotFoundException."""
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user:
            raise EntityNotFoundException("User", user_id)
        return user

    @staticmethod
    def update_user_roles(
        db: Session,
        admin_user: User,
        target_user_id: str,
        role_names: List[str],
        ip_address: Optional[str] = None,
    ) -> User:
        """Assign authorized roles to target user account with audit logging."""
        target_user = AuthService.get_user_by_id(db, target_user_id)

        # Retrieve requested roles
        new_roles = []
        for r_name in role_names:
            role = db.execute(select(Role).where(Role.name == r_name.upper())).scalar_one_or_none()
            if not role:
                raise EntityNotFoundException("Role", r_name)
            new_roles.append(role)

        old_role_names = [r.name for r in target_user.roles]
        target_user.roles = new_roles
        target_user.updated_at = datetime.now(timezone.utc)

        # Audit role update
        SecurityAuditService.record_audit(
            db=db,
            action="USER_ROLES_UPDATED",
            entity_type="USER",
            entity_id=target_user.id,
            user_id=admin_user.id,
            ip_address=ip_address,
            details={
                "previous_roles": old_role_names,
                "new_roles": [r.name for r in new_roles],
                "updated_by": admin_user.email,
            },
            commit=True,
        )
        db.refresh(target_user)
        logger.info(f"User {target_user.email} roles updated by {admin_user.email}: {[r.name for r in new_roles]}")
        return target_user

    @staticmethod
    def update_user_status(
        db: Session,
        admin_user: User,
        target_user_id: str,
        is_active: bool,
        ip_address: Optional[str] = None,
    ) -> User:
        """Activate or deactivate user account with audit logging."""
        target_user = AuthService.get_user_by_id(db, target_user_id)
        prev_status = target_user.is_active
        target_user.is_active = is_active
        target_user.updated_at = datetime.now(timezone.utc)

        # Audit status modification
        SecurityAuditService.record_audit(
            db=db,
            action="USER_STATUS_UPDATED",
            entity_type="USER",
            entity_id=target_user.id,
            user_id=admin_user.id,
            ip_address=ip_address,
            details={
                "previous_status": prev_status,
                "new_status": is_active,
                "modified_by": admin_user.email,
            },
            commit=True,
        )
        db.refresh(target_user)
        logger.info(f"User {target_user.email} active status set to {is_active} by {admin_user.email}")
        return target_user

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
