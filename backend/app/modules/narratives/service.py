"""Coordinated Narrative Detection and Network Graph Intelligence."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Set
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.modules.narratives.models import (
    NarrativeCluster,
    NarrativeClusterReport,
    ThreatIndicator,
)
from backend.app.modules.narratives.schemas import (
    NarrativeClusterOut,
    NarrativeClusterDetailOut,
    ClusterReportSummaryOut,
    ThreatIndicatorOut,
    NarrativeGraphOut,
    GraphNode,
    GraphEdge,
)
from backend.app.modules.reporting.models import Report, UploadedEvidence
from backend.app.modules.ai_engine.service import AIEngineService


class NarrativesService:
    """Discovers emerging coordinated disinformation patterns and semantic clustering."""

    @classmethod
    def scan_and_cluster_reports(cls, db: Session, lookback_hours: int = 72) -> int:
        """Scan recent submissions, identify semantic and media near-duplicates, and synthesize clusters."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        reports = list(
            db.execute(select(Report).where(Report.created_at >= cutoff).order_by(desc(Report.created_at))).scalars().all()
        )

        if len(reports) < 2:
            return 0

        provider = AIEngineService.get_provider()
        clusters_formed = 0

        # Map existing report cluster assignments to avoid redundant clustering
        existing_assignments = {
            cr.report_id: cr.cluster_id
            for cr in db.execute(select(NarrativeClusterReport)).scalars().all()
        }

        # Compare pairs of unclustered reports
        for i in range(len(reports)):
            for j in range(i + 1, len(reports)):
                rep_a = reports[i]
                rep_b = reports[j]

                # 1. Check text similarity
                text_a = f"{rep_a.title} {rep_a.content_text}"
                text_b = f"{rep_b.title} {rep_b.content_text}"
                sim = provider.calculate_similarity(text_a, text_b)

                # 2. Check identical media fingerprints
                hashes_a = {e.sha256_hash for e in rep_a.evidence_items}
                hashes_b = {e.sha256_hash for e in rep_b.evidence_items}
                shared_media = hashes_a.intersection(hashes_b)

                # Matching criteria: high text similarity (>= 0.35) OR exact identical media hash
                if sim >= 0.35 or bool(shared_media):
                    cluster_id = existing_assignments.get(rep_a.id) or existing_assignments.get(rep_b.id)

                    if not cluster_id:
                        # Determine timestamps
                        dates = [d for d in [rep_a.incident_date, rep_b.incident_date, rep_a.created_at, rep_b.created_at] if d]
                        first_dt = min(dates) if dates else datetime.now(timezone.utc)
                        last_dt = max(dates) if dates else datetime.now(timezone.utc)

                        # Create new NarrativeCluster
                        cluster = NarrativeCluster(
                            cluster_title=f"Coordinated Narrative: {rep_a.title[:60]}...",
                            summary=f"Clustered narrative aggregating similar reports from {rep_a.nigerian_state or 'National'} and {rep_b.nigerian_state or 'National'}.",
                            velocity_score=1.5,
                            amplification_pattern="SYNCHRONIZED_POSTING" if rep_a.nigerian_state != rep_b.nigerian_state else "LOCALIZED_SURGE",
                            geographic_scope=list({s for s in [rep_a.nigerian_state, rep_b.nigerian_state] if s}),
                            status="ACTIVE",
                            verification_status="UNVERIFIED",
                            first_reported_at=first_dt,
                            last_reported_at=last_dt,
                        )
                        db.add(cluster)
                        db.flush()
                        cluster_id = cluster.id
                        clusters_formed += 1

                        # Assign rep_a
                        assoc_a = NarrativeClusterReport(cluster_id=cluster_id, report_id=rep_a.id, similarity_score=1.0)
                        db.add(assoc_a)
                        existing_assignments[rep_a.id] = cluster_id

                        # Assign rep_b
                        assoc_b = NarrativeClusterReport(cluster_id=cluster_id, report_id=rep_b.id, similarity_score=sim if sim > 0 else 0.9)
                        db.add(assoc_b)
                        existing_assignments[rep_b.id] = cluster_id

                        # Threat indicators
                        if shared_media:
                            db.add(ThreatIndicator(
                                cluster_id=cluster_id,
                                indicator_type="REPEATED_MEDIA_AMPLIFICATION",
                                evidence_detail=f"Identical media asset with SHA-256 fingerprint {list(shared_media)[0][:16]}... recirculated across multiple reports.",
                                confidence_score=0.95,
                            ))

                        if rep_a.nigerian_state and rep_b.nigerian_state and rep_a.nigerian_state != rep_b.nigerian_state:
                            db.add(ThreatIndicator(
                                cluster_id=cluster_id,
                                indicator_type="CROSS_PLATFORM_SPIKE",
                                evidence_detail=f"Narrative spreading across disparate states ({rep_a.nigerian_state} and {rep_b.nigerian_state}) within a compressed timeframe.",
                                confidence_score=0.80,
                            ))
                    else:
                        # Link rep_b if not already linked
                        if rep_b.id not in existing_assignments:
                            assoc_b = NarrativeClusterReport(cluster_id=cluster_id, report_id=rep_b.id, similarity_score=sim if sim > 0 else 0.85)
                            db.add(assoc_b)
                            existing_assignments[rep_b.id] = cluster_id

        db.commit()
        logger.info(f"Narrative scan completed. Formed/updated {clusters_formed} cluster(s).")
        return clusters_formed

    @staticmethod
    def get_clusters(db: Session, skip: int = 0, limit: int = 50) -> List[NarrativeClusterOut]:
        """List active narrative clusters."""
        clusters = list(
            db.execute(select(NarrativeCluster).order_by(desc(NarrativeCluster.created_at)).offset(skip).limit(limit)).scalars().all()
        )
        results = []
        for c in clusters:
            results.append(
                NarrativeClusterOut(
                    id=c.id,
                    cluster_title=c.cluster_title,
                    summary=c.summary,
                    velocity_score=c.velocity_score,
                    amplification_pattern=c.amplification_pattern,
                    geographic_scope=c.geographic_scope or [],
                    status=getattr(c, "status", "ACTIVE"),
                    verification_status=getattr(c, "verification_status", "UNVERIFIED"),
                    first_reported_at=getattr(c, "first_reported_at", None),
                    last_reported_at=getattr(c, "last_reported_at", None),
                    assigned_analyst_id=getattr(c, "assigned_analyst_id", None),
                    reports_count=len(c.cluster_reports),
                    threat_indicators_count=len(c.threat_indicators),
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )
        return results

    @staticmethod
    def get_cluster_detail(db: Session, cluster_id: str) -> Optional[NarrativeClusterDetailOut]:
        """Retrieve full cluster details with constituent reports and threat indicators."""
        cluster = db.execute(select(NarrativeCluster).where(NarrativeCluster.id == cluster_id)).scalar_one_or_none()
        if not cluster:
            return None

        # Fetch report details
        reports_summary = []
        for cr in cluster.cluster_reports:
            rep = db.execute(select(Report).where(Report.id == cr.report_id)).scalar_one_or_none()
            if rep:
                reports_summary.append(
                    ClusterReportSummaryOut(
                        report_id=rep.id,
                        reference_number=rep.reference_number,
                        title=rep.title,
                        nigerian_state=rep.nigerian_state,
                        similarity_score=cr.similarity_score,
                        incident_date=rep.incident_date,
                    )
                )

        return NarrativeClusterDetailOut(
            id=cluster.id,
            cluster_title=cluster.cluster_title,
            summary=cluster.summary,
            velocity_score=cluster.velocity_score,
            amplification_pattern=cluster.amplification_pattern,
            geographic_scope=cluster.geographic_scope or [],
            status=getattr(cluster, "status", "ACTIVE"),
            verification_status=getattr(cluster, "verification_status", "UNVERIFIED"),
            first_reported_at=getattr(cluster, "first_reported_at", None),
            last_reported_at=getattr(cluster, "last_reported_at", None),
            assigned_analyst_id=getattr(cluster, "assigned_analyst_id", None),
            reports_count=len(cluster.cluster_reports),
            threat_indicators_count=len(cluster.threat_indicators),
            created_at=cluster.created_at,
            updated_at=cluster.updated_at,
            cluster_reports=reports_summary,
            threat_indicators=[ThreatIndicatorOut.model_validate(ti) for ti in cluster.threat_indicators],
        )

    @staticmethod
    def update_cluster(
        db: Session,
        cluster_id: str,
        status: Optional[str] = None,
        verification_status: Optional[str] = None,
        assigned_analyst_id: Optional[str] = None,
        modified_by_user_id: Optional[str] = None,
    ) -> NarrativeCluster:
        """Update cluster management status or analyst assignment."""
        from backend.app.modules.security_audit.service import SecurityAuditService
        cluster = db.execute(select(NarrativeCluster).where(NarrativeCluster.id == cluster_id)).scalar_one_or_none()
        if not cluster:
            raise EntityNotFoundException("NarrativeCluster", cluster_id)

        if status:
            cluster.status = status.upper()
        if verification_status:
            cluster.verification_status = verification_status.upper()
        if assigned_analyst_id:
            cluster.assigned_analyst_id = assigned_analyst_id

        cluster.updated_at = datetime.now(timezone.utc)

        SecurityAuditService.record_audit(
            db=db,
            action="NARRATIVE_CLUSTER_UPDATED",
            entity_type="NARRATIVE_CLUSTER",
            entity_id=cluster.id,
            user_id=modified_by_user_id,
            details={
                "status": cluster.status,
                "verification_status": cluster.verification_status,
                "assigned_analyst_id": cluster.assigned_analyst_id,
            },
            commit=True,
        )
        db.refresh(cluster)
        logger.info(f"Narrative cluster {cluster.id} updated: status={cluster.status}, analyst={cluster.assigned_analyst_id}")
        return cluster

    @staticmethod
    def get_graph_data(db: Session, limit_clusters: int = 20) -> NarrativeGraphOut:
        """Generate graph structure representing clusters, reports, and similarity relationships."""
        clusters = list(
            db.execute(select(NarrativeCluster).order_by(desc(NarrativeCluster.created_at)).limit(limit_clusters)).scalars().all()
        )

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        seen_nodes: Set[str] = set()

        for c in clusters:
            if c.id not in seen_nodes:
                nodes.append(GraphNode(
                    id=c.id,
                    label=c.cluster_title[:30] + "...",
                    type="CLUSTER",
                    group=c.amplification_pattern,
                    value=float(len(c.cluster_reports) * 2),
                ))
                seen_nodes.add(c.id)

            for cr in c.cluster_reports:
                rep = db.execute(select(Report).where(Report.id == cr.report_id)).scalar_one_or_none()
                if rep and rep.id not in seen_nodes:
                    nodes.append(GraphNode(
                        id=rep.id,
                        label=rep.reference_number,
                        type="REPORT",
                        group=rep.nigerian_state or "National",
                        value=1.0,
                    ))
                    seen_nodes.add(rep.id)

                if rep:
                    edges.append(GraphEdge(
                        source=c.id,
                        target=rep.id,
                        weight=cr.similarity_score,
                        relationship="BELONGS_TO",
                    ))

        report_nodes_count = sum(1 for n in nodes if n.type == "REPORT")
        return NarrativeGraphOut(
            nodes=nodes,
            edges=edges,
            total_clusters=len(clusters),
            total_connected_reports=report_nodes_count,
        )
