"""Provider Factory for CivicShield AI Misinformation Intelligence Engine."""

from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.modules.ai_engine.providers.base import BaseAIProvider
from backend.app.modules.ai_engine.providers.local_heuristic import LocalHeuristicAIProvider
from backend.app.modules.ai_engine.providers.gemini_provider import GeminiAIProvider
from backend.app.modules.ai_engine.providers.dev_adapter import DevelopmentAdapterAIProvider


def get_ai_provider(provider_type: Optional[str] = None) -> BaseAIProvider:
    """
    Instantiate and return the appropriate AI Provider according to configuration.
    Supported types: 'local', 'gemini', 'dev_adapter'.
    """
    ptype = (provider_type or settings.AI_PROVIDER_TYPE or "local").lower().strip()

    if ptype == "gemini":
        if settings.GEMINI_API_KEY:
            logger.info("Initializing Google Gemini Cloud AI Provider.")
            return GeminiAIProvider(api_key=settings.GEMINI_API_KEY)
        else:
            logger.warning(
                "AI_PROVIDER_TYPE is 'gemini' but GEMINI_API_KEY is not set. "
                "Falling back safely to LocalHeuristicAIProvider."
            )
            return LocalHeuristicAIProvider()

    elif ptype in ["dev_adapter", "test", "mock"]:
        if settings.ENVIRONMENT == "production":
            logger.error("Attempted to load dev_adapter in production! Enforcing LocalHeuristicAIProvider.")
            return LocalHeuristicAIProvider()
        logger.info("Initializing DevelopmentAdapterAIProvider for testing harness.")
        return DevelopmentAdapterAIProvider()

    # Default to Local Heuristic
    return LocalHeuristicAIProvider()
