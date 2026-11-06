"""Coordinated Narrative Detection API Endpoints."""

import asyncio
from typing import List, Optional
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.database import get_db, SessionLocal
from backend.app.core.dependencies import require_permission
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.models import User
from backend.app.modules.narratives.schemas import (
    NarrativeClusterOut,
    NarrativeClusterDetailOut,
    NarrativeGraphOut,
    ClusterUpdateRequest,
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


@router.patch(
    "/clusters/{cluster_id}",
    response_model=APIResponse[NarrativeClusterDetailOut],
    summary="Update narrative cluster status or analyst assignment (Command Centre)",
)
def update_narrative_cluster(
    cluster_id: str,
    payload: ClusterUpdateRequest,
    current_user: User = Depends(require_permission("narratives:view")),
    db: Session = Depends(get_db),
) -> APIResponse[NarrativeClusterDetailOut]:
    """Update cluster investigation status, verification status, or analyst assignment."""
    updated = NarrativesService.update_cluster(
        db=db,
        cluster_id=cluster_id,
        status=payload.status,
        verification_status=payload.verification_status,
        assigned_analyst_id=payload.assigned_analyst_id,
        modified_by_user_id=current_user.id,
    )
    detail = NarrativesService.get_cluster_detail(db=db, cluster_id=cluster_id)
    if ws_manager.active_connections:
        asyncio.create_task(ws_manager.broadcast("CLUSTER_UPDATED", detail.model_dump(mode="json")))
    return APIResponse(
        data=detail,
        message=f"Narrative cluster '{cluster_id}' updated successfully.",
    )


class NarrativeWebSocketManager:
    """Manages active live WebSocket connections and broadcasts real-time intelligence events."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: dict) -> None:
        """Push real-time event to all connected clients."""
        payload = json.dumps({"event": event_type, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()})
        async with self._lock:
            dead_connections = []
            for ws in self.active_connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_connections.append(ws)
            for dead in dead_connections:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)


ws_manager = NarrativeWebSocketManager()


@router.websocket("/ws")
async def narrative_pulse_websocket(websocket: WebSocket) -> None:
    """Real-time live WebSocket channel for Narrative Pulse Command Centre dashboard."""
    await ws_manager.connect(websocket)
    try:
        with SessionLocal() as db:
            clusters = NarrativesService.get_clusters(db=db, limit=10)
            initial_payload = {
                "event": "INITIAL_CLUSTERS",
                "clusters_count": len(clusters),
                "clusters": [c.model_dump(mode="json") for c in clusters],
            }
            await websocket.send_text(json.dumps(initial_payload))

        while True:
            # Keep-alive loop listening for client ping/refresh requests
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "refresh":
                with SessionLocal() as db:
                    fresh_clusters = NarrativesService.get_clusters(db=db, limit=10)
                    await websocket.send_text(json.dumps({
                        "event": "CLUSTER_REFRESH",
                        "clusters": [c.model_dump(mode="json") for c in fresh_clusters],
                    }))
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
