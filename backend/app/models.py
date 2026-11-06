"""Central registry aggregating all SQLAlchemy models for Alembic and DB metadata."""

from backend.app.core.database import Base
from backend.app.modules.auth.models import User, Role, Permission, user_roles, role_permissions, RevokedToken
from backend.app.modules.reporting.models import Report, UploadedEvidence, ReportStatusHistory
from backend.app.modules.registry.models import OfficialDocument, DocumentVersion, TrustedSource
from backend.app.modules.verification.models import Claim, VerificationRecord, Investigation, VerificationRecommendation
from backend.app.modules.narratives.models import NarrativeCluster, NarrativeClusterReport, ThreatIndicator
from backend.app.modules.notifications.models import Alert, NotificationPreference, NotificationDelivery, AlertApprovalRecord
from backend.app.modules.security_audit.models import AuditLog, SecurityEvent

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "RevokedToken",
    "Report",
    "UploadedEvidence",
    "ReportStatusHistory",
    "OfficialDocument",
    "DocumentVersion",
    "TrustedSource",
    "Claim",
    "VerificationRecord",
    "Investigation",
    "VerificationRecommendation",
    "NarrativeCluster",
    "NarrativeClusterReport",
    "ThreatIndicator",
    "Alert",
    "NotificationPreference",
    "NotificationDelivery",
    "AlertApprovalRecord",
    "AuditLog",
    "SecurityEvent",
]
