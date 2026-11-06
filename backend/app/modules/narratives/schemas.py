"""Pydantic schemas for Coordinated Narrative Detection and Threat Intelligence."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ThreatIndicatorOut(BaseModel):
    """Specific technical pattern identified within an amplified narrative."""

    id: str
    indicator_type: str
    evidence_detail: str
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ClusterReportSummaryOut(BaseModel):
    """Summary of a report linked to a narrative cluster."""

    report_id: str
    reference_number: str
    title: str
    nigerian_state: Optional[str] = None
    similarity_score: float
    incident_date: Optional[datetime] = None


class NarrativeClusterOut(BaseModel):
    """Summary of an active narrative cluster."""

    id: str
    cluster_title: str
    summary: str
    velocity_score: float
    amplification_pattern: str
    geographic_scope: Optional[list] = []
    status: str = "ACTIVE"
    verification_status: str = "UNVERIFIED"
    first_reported_at: Optional[datetime] = None
    last_reported_at: Optional[datetime] = None
    assigned_analyst_id: Optional[str] = None
    reports_count: int = 0
    threat_indicators_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClusterUpdateRequest(BaseModel):
    """Payload for updating cluster status or assigning analyst."""

    status: Optional[str] = None
    verification_status: Optional[str] = None
    assigned_analyst_id: Optional[str] = None


class NarrativeClusterDetailOut(NarrativeClusterOut):
    """Detailed cluster inspection with constituent reports and technical threat indicators."""

    cluster_reports: List[ClusterReportSummaryOut] = []
    threat_indicators: List[ThreatIndicatorOut] = []


class GraphNode(BaseModel):
    """Graph node representing an entity (Cluster or Report)."""

    id: str
    label: str
    type: str  # "CLUSTER" or "REPORT"
    group: Optional[str] = None
    value: float = 1.0


class GraphEdge(BaseModel):
    """Graph edge representing similarity or association."""

    source: str
    target: str
    weight: float
    relationship: str


class NarrativeGraphOut(BaseModel):
    """Network graph payload for visualization in the Command Centre."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_clusters: int
    total_connected_reports: int
