"""add_trusted_sources_recommendations_and_alert_history

Revision ID: a32acb5b8255
Revises: 51b55dfbf272
Create Date: 2026-11-06 16:15:58.148058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a32acb5b8255'
down_revision: Union[str, None] = '51b55dfbf272'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. trusted_sources
    if "trusted_sources" not in existing_tables:
        op.create_table(
            "trusted_sources",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(255), unique=True, index=True, nullable=False),
            sa.Column("url", sa.String(512), nullable=False),
            sa.Column("category", sa.String(64), default="ELECTORAL_COMMISSION", index=True, nullable=False),
            sa.Column("verification_status", sa.String(32), default="VERIFIED", index=True, nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
            sa.Column("last_retrieved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("registered_by_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # 2. verification_recommendations
    if "verification_recommendations" not in existing_tables:
        op.create_table(
            "verification_recommendations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("claim_id", sa.String(36), sa.ForeignKey("claims.id", ondelete="CASCADE"), index=True, nullable=False),
            sa.Column("analyst_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False),
            sa.Column("recommended_decision", sa.String(32), index=True, nullable=False),
            sa.Column("justification_notes", sa.Text(), nullable=False),
            sa.Column("proposed_clarification", sa.Text(), nullable=False),
            sa.Column("official_document_id", sa.String(36), sa.ForeignKey("official_documents.id", ondelete="SET NULL"), nullable=True),
            sa.Column("evidence_sources_consulted", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(32), default="PENDING_REVIEW", index=True, nullable=False),
            sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True),
            sa.Column("reviewer_notes", sa.Text(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # 3. alert_approval_records
    if "alert_approval_records" not in existing_tables:
        op.create_table(
            "alert_approval_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), index=True, nullable=False),
            sa.Column("action", sa.String(32), nullable=False),
            sa.Column("officer_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False),
            sa.Column("comments", sa.Text(), nullable=True),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # 4. Additive columns
    if "reports" in existing_tables:
        report_cols = [c["name"] for c in inspector.get_columns("reports")]
        if "assigned_analyst_id" not in report_cols:
            op.add_column("reports", sa.Column("assigned_analyst_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))

    if "official_documents" in existing_tables:
        doc_cols = [c["name"] for c in inspector.get_columns("official_documents")]
        if "trusted_source_id" not in doc_cols:
            op.add_column("official_documents", sa.Column("trusted_source_id", sa.String(36), sa.ForeignKey("trusted_sources.id", ondelete="SET NULL"), nullable=True))

    if "narrative_clusters" in existing_tables:
        nc_cols = [c["name"] for c in inspector.get_columns("narrative_clusters")]
        if "status" not in nc_cols:
            op.add_column("narrative_clusters", sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False))
        if "verification_status" not in nc_cols:
            op.add_column("narrative_clusters", sa.Column("verification_status", sa.String(32), server_default="UNVERIFIED", nullable=False))
        if "first_reported_at" not in nc_cols:
            op.add_column("narrative_clusters", sa.Column("first_reported_at", sa.DateTime(timezone=True), nullable=True))
        if "last_reported_at" not in nc_cols:
            op.add_column("narrative_clusters", sa.Column("last_reported_at", sa.DateTime(timezone=True), nullable=True))
        if "assigned_analyst_id" not in nc_cols:
            op.add_column("narrative_clusters", sa.Column("assigned_analyst_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))


def downgrade() -> None:
    pass
