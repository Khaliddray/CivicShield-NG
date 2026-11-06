"""Database initialization and RBAC seed manager."""

from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.core.logging import logger
import backend.app.models  # Ensure all models are registered in metadata
from backend.app.modules.auth.models import Role, Permission
from backend.app.common.enums import UserRoleType

# System default permissions catalog
PERMISSIONS_CATALOG = [
    ("reports:create", "Submit suspicious electoral reports"),
    ("reports:view_own", "View status of own submitted reports"),
    ("reports:view_all", "View all submitted reports in Command Centre"),
    ("reports:manage", "Update report investigation status, assign analysts, or withdraw reports"),
    ("claims:analyze", "Run AI claim extraction and similarity comparison"),
    ("claims:verify", "Record authoritative verification decisions"),
    ("recommendations:create", "Create analyst verification recommendations"),
    ("recommendations:review", "Review, approve or reject analyst verification recommendations"),
    ("registry:view", "View authenticated official documents and trusted sources"),
    ("registry:manage", "Publish and certify official electoral announcements"),
    ("sources:manage", "Register, edit, and manage trusted official information sources"),
    ("alerts:create", "Draft early warning misinformation alerts"),
    ("alerts:approve", "Approve and broadcast early warning alerts"),
    ("alerts:withdraw", "Withdraw or clarify existing alerts"),
    ("narratives:view", "Inspect coordinated narrative clusters"),
    ("audit:read", "Read tamper-evident audit logs"),
    ("security:manage", "Inspect security events and manage threat mitigation"),
    ("users:manage", "Manage platform user accounts, roles, and administrative statuses"),
    ("system:admin", "Full platform administration and configuration"),
]

# Role to permission mapping
ROLE_PERMISSIONS_MAPPING = {
    UserRoleType.CITIZEN.value: [
        "reports:create",
        "reports:view_own",
        "registry:view",
    ],
    UserRoleType.ANALYST.value: [
        "reports:create",
        "reports:view_own",
        "reports:view_all",
        "reports:manage",
        "claims:analyze",
        "recommendations:create",
        "registry:view",
        "alerts:create",
        "narratives:view",
    ],
    UserRoleType.VERIFICATION_OFFICER.value: [
        "reports:view_all",
        "reports:manage",
        "claims:analyze",
        "claims:verify",
        "recommendations:create",
        "recommendations:review",
        "registry:view",
        "registry:manage",
        "sources:manage",
        "alerts:create",
        "alerts:approve",
        "alerts:withdraw",
        "narratives:view",
    ],
    UserRoleType.SECURITY_OFFICER.value: [
        "reports:view_all",
        "audit:read",
        "security:manage",
        "narratives:view",
    ],
    UserRoleType.ADMINISTRATOR.value: [
        slug for slug, _ in PERMISSIONS_CATALOG
    ],
}


def seed_rbac(db: Session) -> None:
    """Seed initial permissions, roles, and default associations if not present."""
    logger.info("Checking and seeding RBAC roles and permissions...")

    # 1. Seed Permissions
    permissions_map = {}
    for slug, desc in PERMISSIONS_CATALOG:
        existing = db.execute(select(Permission).where(Permission.slug == slug)).scalar_one_or_none()
        if not existing:
            perm = Permission(slug=slug, description=desc)
            db.add(perm)
            db.flush()
            permissions_map[slug] = perm
            logger.info(f"Seeded permission: {slug}")
        else:
            permissions_map[slug] = existing

    # 2. Seed Roles
    role_descriptions = {
        UserRoleType.CITIZEN.value: "Nigerian Citizen with public reporting and verification access.",
        UserRoleType.ANALYST.value: "Intelligence analyst conducting claim extraction and narrative monitoring.",
        UserRoleType.VERIFICATION_OFFICER.value: "Authorized institutional fact-checker and verification officer.",
        UserRoleType.SECURITY_OFFICER.value: "Security administrator monitoring platform and database integrity.",
        UserRoleType.ADMINISTRATOR.value: "Lead platform administrator with comprehensive institutional access.",
    }

    for role_name, description in role_descriptions.items():
        existing_role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
        if not existing_role:
            role = Role(name=role_name, description=description)
            # Assign permissions
            target_slugs = ROLE_PERMISSIONS_MAPPING.get(role_name, [])
            role.permissions = [permissions_map[slug] for slug in target_slugs if slug in permissions_map]
            db.add(role)
            logger.info(f"Seeded role: {role_name} with {len(role.permissions)} permissions")
        else:
            # Update permissions if necessary
            target_slugs = ROLE_PERMISSIONS_MAPPING.get(role_name, [])
            existing_slugs = {p.slug for p in existing_role.permissions}
            for slug in target_slugs:
                if slug in permissions_map and slug not in existing_slugs:
                    existing_role.permissions.append(permissions_map[slug])

    db.commit()
    logger.info("RBAC seeding complete.")


def init_database() -> None:
    """Create all schema tables and seed essential records safely."""
    from sqlalchemy import text
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    # Safe additive column checks for SQLite / PostgreSQL
    with engine.begin() as conn:
        try:
            # Check SQLite tables
            is_sqlite = str(engine.url).startswith("sqlite")
            if is_sqlite:
                # 1. reports.assigned_analyst_id
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(reports);")).fetchall()]
                if "assigned_analyst_id" not in cols:
                    conn.execute(text("ALTER TABLE reports ADD COLUMN assigned_analyst_id VARCHAR(36) REFERENCES users(id);"))
                
                # 2. official_documents.trusted_source_id
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(official_documents);")).fetchall()]
                if "trusted_source_id" not in cols:
                    conn.execute(text("ALTER TABLE official_documents ADD COLUMN trusted_source_id VARCHAR(36) REFERENCES trusted_sources(id);"))

                # 3. narrative_clusters columns
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(narrative_clusters);")).fetchall()]
                if "status" not in cols:
                    conn.execute(text("ALTER TABLE narrative_clusters ADD COLUMN status VARCHAR(32) DEFAULT 'ACTIVE' NOT NULL;"))
                if "verification_status" not in cols:
                    conn.execute(text("ALTER TABLE narrative_clusters ADD COLUMN verification_status VARCHAR(32) DEFAULT 'UNVERIFIED' NOT NULL;"))
                if "first_reported_at" not in cols:
                    conn.execute(text("ALTER TABLE narrative_clusters ADD COLUMN first_reported_at DATETIME;"))
                if "last_reported_at" not in cols:
                    conn.execute(text("ALTER TABLE narrative_clusters ADD COLUMN last_reported_at DATETIME;"))
                if "assigned_analyst_id" not in cols:
                    conn.execute(text("ALTER TABLE narrative_clusters ADD COLUMN assigned_analyst_id VARCHAR(36) REFERENCES users(id);"))
        except Exception as e:
            logger.warning(f"Additive migration check note: {e}")

    with SessionLocal() as db:
        seed_rbac(db)


if __name__ == "__main__":
    init_database()
