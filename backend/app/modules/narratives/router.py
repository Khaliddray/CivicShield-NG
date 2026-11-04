"""Coordinated Narrative Detection API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.narratives.schemas import (
    NarrativeClusterOut,
    NarrativeClusterDetailOut,
    NarrativeGraphOut,
)
from backend.app.modules.narratives.service import NarrativesService

router = APIRouter(prefix="/narratives", tags=["Coordinated Narrative Intelligence"])


@router.get(
    "/clusters",
    response_model=APIResponse[List[NarrativeClusterOut]],
    summary="List active coordinated narrative clusters (Command Centre)",
)
def list_clusters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("narratives:view")),
    db: Session = Depends(get_db),
) -> APIResponse[List[NarrativeClusterOut]]:
    """Command Centre analytical view of grouped reports, velocity surges, and amplification patterns."""
    skip = (page - 1) * page_size
    clusters = NarrativesService.get_clusters(db=db, skip=skip, limit=page_size)
    return APIResponse(
        data=clusters,
        message=f"Retrieved {len(clusters)} active narrative cluster(s).",
    )


@router.get(
    "/clusters/{cluster_id}",
    response_model=APIResponse[NarrativeClusterDetailOut],
    summary="Inspect constituent reports and technical threat indicators of a cluster",
)
def get_cluster_detail(
    cluster_id: str,
    current_user: User = Depends(require_permission("narratives:view")),
    db: Session = Depends(get_db),
) -> APIResponse[NarrativeClusterDetailOut]:
    """Inspect full constituent report grouping and identified technical indicators."""
    cluster = NarrativesService.get_cluster_detail(db=db, cluster_id=cluster_id)
    if not cluster:
        raise EntityNotFoundException("NarrativeCluster", cluster_id)

    return APIResponse(
        data=cluster,
        message="Narrative cluster details retrieved successfully.",
    )


@router.get(
    "/graph",
    response_model=APIResponse[NarrativeGraphOut],
    summary="Retrieve network relationship graph data for Command Centre visualizer",
)
def get_narrative_graph(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_permission("narratives:view")),
    db: Session = Depends(get_db),
) -> APIResponse[NarrativeGraphOut]:
    """Network graph payload providing nodes (clusters, reports) and similarity edges for D3 / Recharts rendering."""
    graph = NarrativesService.get_graph_data(db=db, limit_clusters=limit)
    return APIResponse(
        data=graph,
        message="Narrative relationship graph generated successfully.",
    )


@router.post(
    "/scan",
    response_model=APIResponse[dict],
    summary="Trigger clustering discovery scan on recent reports",
)
def trigger_clustering_scan(
    lookback_hours: int = Query(72, ge=1, le=168),
    current_user: User = Depends(require_permission("narratives:view")),
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """Execute clustering engine comparing recent report narratives and shared media assets."""
    count = NarrativesService.scan_and_cluster_reports(db=db, lookback_hours=lookback_hours)
    return APIResponse(
        data={"clusters_updated_or_formed": count, "lookback_hours": lookback_hours},
        message=f"Narrative scan completed. Formed or updated {count} cluster(s).",
    )
