"""Cryptographic security utilities: Argon2id password hashing, JWT lifecycle, and integrity hashing."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationException

# Initialize Argon2id password hasher with configured parameters
_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_access_token(subject: str, additional_claims: Optional[Dict[str, Any]] = None, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed, short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
        "jti": secrets.token_hex(16),
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed, longer-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "iat"]},
        )
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationException(f"Invalid token type. Expected '{expected_type}', got '{token_type}'.")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Authentication token has expired.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationException(f"Invalid authentication token: {str(exc)}")


def hash_ip_for_privacy(ip_address: Optional[str]) -> Optional[str]:
    """Hash an IP address with a secret salt to prevent voter tracking while enabling anti-spam detection."""
    if not ip_address:
        return None
    salted = f"{settings.SECRET_KEY}:{ip_address}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


def compute_audit_hash(previous_hash: str, action: str, entity_id: str, timestamp_str: str) -> str:
    """Compute cryptographic hash chaining for tamper-evident audit ledger."""
    entry_payload = f"{previous_hash}|{action}|{entity_id}|{timestamp_str}"
    return hashlib.sha256(entry_payload.encode("utf-8")).hexdigest()


_REVOKED_TOKENS_MEM_CACHE: set = set()


def get_token_identifier(token: str, payload: Optional[Dict[str, Any]] = None) -> str:
    """Extract jti claim or deterministic sha256 token fingerprint."""
    if payload and "jti" in payload:
        return str(payload["jti"])
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        if "jti" in unverified:
            return str(unverified["jti"])
    except Exception:
        pass
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def revoke_token(
    db: Any,
    token: str,
    user_id: Optional[str] = None,
    reason: str = "USER_LOGOUT",
) -> None:
    """Revoke an active JWT token and add it to the cryptographic blacklist."""
    from backend.app.modules.auth.models import RevokedToken
    from sqlalchemy import select

    token_id = get_token_identifier(token)
    _REVOKED_TOKENS_MEM_CACHE.add(token_id)

    # Determine expiry
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        if "exp" in unverified:
            expires_at = datetime.fromtimestamp(unverified["exp"], tz=timezone.utc)
    except Exception:
        pass

    existing = db.execute(select(RevokedToken).where(RevokedToken.token_identifier == token_id)).scalar_one_or_none()
    if not existing:
        revocation = RevokedToken(
            token_identifier=token_id,
            user_id=user_id,
            revoked_at=now,
            expires_at=expires_at,
            reason=reason,
        )
        db.add(revocation)
        try:
            db.commit()
        except Exception:
            db.rollback()


def is_token_revoked(db: Any, token: str) -> bool:
    """Check if token identifier exists in memory cache or persisted revoked_tokens table."""
    from backend.app.modules.auth.models import RevokedToken
    from sqlalchemy import select

    token_id = get_token_identifier(token)
    if token_id in _REVOKED_TOKENS_MEM_CACHE:
        return True

    existing = db.execute(select(RevokedToken).where(RevokedToken.token_identifier == token_id)).scalar_one_or_none()
    if existing:
        _REVOKED_TOKENS_MEM_CACHE.add(token_id)
        return True

    return False
