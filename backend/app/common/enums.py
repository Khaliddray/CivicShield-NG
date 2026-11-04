"""Core enumeration types for CivicShield NG domain models."""

from enum import Enum


class UserRoleType(str, Enum):
    """System user roles."""

    CITIZEN = "CITIZEN"
    ANALYST = "ANALYST"
    VERIFICATION_OFFICER = "VERIFICATION_OFFICER"
    SECURITY_OFFICER = "SECURITY_OFFICER"
    ADMINISTRATOR = "ADMINISTRATOR"


class ReportStatus(str, Enum):
    """Lifecycle status of a citizen submission."""

    SUBMITTED = "SUBMITTED"
    ANALYZING = "ANALYZING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class PriorityLevel(str, Enum):
    """Priority scoring for submissions and investigations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VerificationDecision(str, Enum):
    """Formal verification states of electoral claims."""

    UNVERIFIED = "UNVERIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    WITHDRAWN = "WITHDRAWN"


class ClaimCategory(str, Enum):
    """Electoral domain taxonomy."""

    RESULTS_ANNOUNCEMENT = "RESULTS_ANNOUNCEMENT"
    VOTER_SUPPRESSION = "VOTER_SUPPRESSION"
    INEC_OPERATIONS = "INEC_OPERATIONS"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    LOGISTICS_DELAY = "LOGISTICS_DELAY"
    DISINFORMATION_CAMPAIGN = "DISINFORMATION_CAMPAIGN"
    GENERAL_ELECTORAL = "GENERAL_ELECTORAL"


class AlertSeverity(str, Enum):
    """Severity classification for early warnings."""

    INFORMATIONAL = "INFORMATIONAL"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertCategory(str, Enum):
    """Category classification for public warnings."""

    EMERGING_SUSPICIOUS = "EMERGING_SUSPICIOUS"
    CONFIRMED_MISINFORMATION = "CONFIRMED_MISINFORMATION"
    OFFICIAL_CLARIFICATION = "OFFICIAL_CLARIFICATION"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"


class AlertStatus(str, Enum):
    """Approval lifecycle of an early warning alert."""

    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    UPDATED = "UPDATED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class AlertScope(str, Enum):
    """Geographic targeting scope."""

    NATIONAL = "NATIONAL"
    STATE_SPECIFIC = "STATE_SPECIFIC"
    ZONAL = "ZONAL"


class MediaType(str, Enum):
    """Uploaded media classification."""

    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"


class SecurityEventType(str, Enum):
    """Security and audit event types."""

    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"
    BRUTE_FORCE_SUSPECTED = "BRUTE_FORCE_SUSPECTED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    TAMPER_DETECTED = "TAMPER_DETECTED"
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    ALERT_PUBLISHED = "ALERT_PUBLISHED"
    SYSTEM_CONFIG_CHANGED = "SYSTEM_CONFIG_CHANGED"
