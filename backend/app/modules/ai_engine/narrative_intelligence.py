"""Narrative Pulse Threat Intelligence Engine (Section 8).

Supports:
- Grouping candidate reports into thematic narrative clusters
- Generating concise, responsible narrative summaries
- Identifying relevant entities and topics
- Calculating propagation velocity (reports per hour / surge velocity index)
- Identifying emerging threat indicators (e.g. repeated media, synchronized cross-state spikes)
- Strict safeguards against speculative political or foreign actor attribution
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timezone
from backend.app.modules.ai_engine.similarity import SimilarityEngine
from backend.app.modules.ai_engine.claim_extractor import ClaimExtractionEngine
from backend.app.modules.ai_engine.schemas import NarrativePulseClusterSummary

SAFEGUARD_DISCLAIMER = (
    "AI-Generated Threat Intelligence Assessment — For analyst review only. "
    "Narrative clustering reflects topical recurrence, not proof of coordinated intent "
    "or common authorship. Report volume does not establish factual accuracy."
)


class NarrativeIntelligenceEngine:
    """Analytical algorithms supporting CivicShield Live and Narrative Pulse."""

    @classmethod
    def calculate_velocity_score(
        cls,
        report_count: int,
        first_reported_at: Optional[datetime],
        last_reported_at: Optional[datetime],
    ) -> float:
        """
        Calculate propagation velocity score (reports per hour / acceleration index).
        A cluster with 10 reports in 1 hour has high velocity; 10 reports in 72 hours has low velocity.
        """
        if report_count <= 1:
            return 1.0

        if not first_reported_at or not last_reported_at or first_reported_at >= last_reported_at:
            # Assume immediate burst
            return round(float(report_count) * 1.5, 2)

        duration_hours = max((last_reported_at - first_reported_at).total_seconds() / 3600.0, 0.5)
        rate = report_count / duration_hours
        # Scale to index between 1.0 and 10.0
        velocity_index = min(1.0 + (rate * 1.2), 10.0)
        return round(float(velocity_index), 2)

    @classmethod
    def generate_narrative_title_and_summary(
        cls,
        constituent_reports: List[Dict[str, Any]],
        shared_entities: List[str],
    ) -> Tuple[str, str]:
        """
        Synthesize concise, objective narrative title and summary.
        Safeguard: Never use accusatory or partisan language.
        """
        if not constituent_reports:
            return "Unspecified Electoral Narrative", "No constituent reports available."

        first_title = constituent_reports[0].get("title", "")
        # Clean title
        clean_title = re.sub(r"^(BREAKING|URGENT|ALERT|VIRAL):\s*", "", first_title, flags=re.IGNORECASE).strip()
        cluster_title = f"Reported claim regarding: {clean_title[:70]}"

        # Gather distinct states
        states = {
            r.get("nigerian_state")
            for r in constituent_reports
            if r.get("nigerian_state")
        }
        state_text = ", ".join(sorted(states)) if states else "multiple locations"

        entity_text = f" involving {', '.join(shared_entities[:3])}" if shared_entities else ""

        summary = (
            f"Multiple citizen reports ({len(constituent_reports)} submissions) report similar claims "
            f"concerning {clean_title[:80]} across {state_text}{entity_text}. "
            f"{SAFEGUARD_DISCLAIMER}"
        )

        return cluster_title, summary

    @classmethod
    def identify_cluster_entities(cls, reports: List[Dict[str, Any]]) -> List[str]:
        """Extract and aggregate high-frequency entities across reports."""
        entity_counts: Dict[str, int] = {}

        for r in reports:
            text = f"{r.get('title', '')} {r.get('content_text', '')}"
            entities = ClaimExtractionEngine.extract_entities(text, context_state=r.get("nigerian_state"))
            for ent in entities:
                entity_counts[ent] = entity_counts.get(ent, 0) + 1

        # Sort by frequency
        sorted_entities = sorted(entity_counts.keys(), key=lambda e: entity_counts[e], reverse=True)
        return sorted_entities[:5]

    @classmethod
    def detect_threat_indicators(
        cls,
        reports: List[Dict[str, Any]],
        shared_media_hashes: Set[str],
    ) -> List[Dict[str, Any]]:
        """
        Identify technical amplification patterns without making political or attribution inferences.
        """
        indicators = []

        # 1. Repeated Media Fingerprint
        if shared_media_hashes:
            indicators.append({
                "indicator_type": "REPEATED_MEDIA_AMPLIFICATION",
                "evidence_detail": (
                    f"Identical media asset with SHA-256 fingerprint {list(shared_media_hashes)[0][:16]}... "
                    f"recirculated across {len(reports)} independent submissions."
                ),
                "confidence_score": 0.95,
            })

        # 2. Multi-state cross-platform spike
        states = {r.get("nigerian_state") for r in reports if r.get("nigerian_state")}
        if len(states) >= 2:
            indicators.append({
                "indicator_type": "CROSS_PLATFORM_SPIKE",
                "evidence_detail": (
                    f"Narrative observed concurrently across {len(states)} distinct Nigerian states: "
                    f"{', '.join(sorted(states))}."
                ),
                "confidence_score": 0.85,
            })

        # 3. High Volume Surge
        if len(reports) >= 5:
            indicators.append({
                "indicator_type": "HIGH_VOLUME_SURGE",
                "evidence_detail": f"Elevated volume of {len(reports)} similar submissions within monitoring window.",
                "confidence_score": 0.80,
            })

        return indicators
