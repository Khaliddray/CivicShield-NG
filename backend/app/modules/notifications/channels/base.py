"""Pluggable Notification Channel Interface."""

from abc import ABC, abstractmethod
from typing import List
from sqlalchemy.orm import Session
from backend.app.modules.notifications.models import Alert
from backend.app.modules.auth.models import User


class BaseNotificationChannel(ABC):
    """Abstract interface for alert delivery channels (In-App, Push, Email, SMS, WhatsApp)."""

    channel_name: str

    @abstractmethod
    def dispatch(self, alert: Alert, target_users: List[User], db: Session) -> int:
        """Deliver alert to targeted users and return count of successful deliveries."""
        pass
