"""In-App Notification Delivery Channel."""

from typing import List
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.modules.notifications.channels.base import BaseNotificationChannel
from backend.app.modules.notifications.models import Alert, NotificationDelivery
from backend.app.modules.auth.models import User
from backend.app.core.logging import logger


class InAppNotificationChannel(BaseNotificationChannel):
    """In-app alert delivery creating trackable recipient delivery records."""

    channel_name = "IN_APP"

    def dispatch(self, alert: Alert, target_users: List[User], db: Session) -> int:
        """Create in-app notifications for all eligible targeted users."""
        count = 0
        now = datetime.now(timezone.utc)

        for user in target_users:
            delivery = NotificationDelivery(
                alert_id=alert.id,
                recipient_user_id=user.id,
                channel=self.channel_name,
                delivery_status="DELIVERED",
                delivered_at=now,
            )
            db.add(delivery)
            count += 1

        db.flush()
        logger.info(f"Dispatched {count} in-app notification deliveries for alert {alert.alert_reference}")
        return count
