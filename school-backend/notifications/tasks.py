import logging
from celery import shared_task
from .services import send_notification
from users.models import User

logger = logging.getLogger(__name__)

@shared_task(
    bind=True, 
    max_retries=3, 
    default_retry_delay=60, # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True
)
def send_notification_task(self, user_id, title, message, notification_type='GENERAL', channels=None):
    """
    Asynchronous task for sending a single notification.
    """
    try:
        user = User.objects.get(id=user_id)
        send_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            channels=channels
        )
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for notification.")
    except Exception as e:
        logger.error(f"Failed to send notification to User {user_id}: {str(e)}")
        raise self.retry(exc=e)

@shared_task(
    bind=True,
    max_retries=1, # Don't retry the entire batch, let individual tasks retry
    time_limit=1800 # 30 mins
)
def bulk_send_notifications_task(self, user_ids, title, message, notification_type='GENERAL', channels=None):
    """
    Triggers multiple individual notification tasks.
    """
    for user_id in user_ids:
        send_notification_task.delay(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channels=channels
        )
    return f"Enqueued {len(user_ids)} notifications."
