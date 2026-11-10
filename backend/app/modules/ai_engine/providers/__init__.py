"""Pluggable AI Providers package for CivicShield NG."""

from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.providers.local_heuristic import LocalHeuristicAIProvider
from backend.app.modules.ai_engine.providers.gemini import GeminiAIProvider

__all__ = ["BaseAIProvider", "LocalHeuristicAIProvider", "GeminiAIProvider"]
