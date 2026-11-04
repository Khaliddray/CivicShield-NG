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
    ("claims:analyze", "Run AI claim extraction and similarity comparison"),
    ("claims:verify", "Record authoritative verification decisions"),
    ("registry:view", "View authenticated official documents"),
    ("registry:manage", "Publish and certify official electoral announcements"),
    ("alerts:create", "Draft early warning misinformation alerts"),
    ("alerts:approve", "Approve and broadcast early warning alerts"),
    ("alerts:withdraw", "Withdraw or clarify existing alerts"),
    ("narratives:view", "Inspect coordinated narrative clusters"),
    ("audit:read", "Read tamper-evident audit logs"),
    ("security:manage", "Inspect security events and manage threat mitigation"),
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
        "claims:analyze",
        "registry:view",
        "alerts:create",
        "narratives:view",
    ],
    UserRoleType.VERIFICATION_OFFICER.value: [
        "reports:view_all",
        "claims:analyze",
        "claims:verify",
        "registry:view",
        "registry:manage",
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
    """Create all schema tables and seed essential records."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    with SessionLocal() as db:
        seed_rbac(db)


if __name__ == "__main__":
    init_database()
