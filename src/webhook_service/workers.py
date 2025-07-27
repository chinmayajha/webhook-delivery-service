from .config import celery_app
from . import models
from . import services
from .config import SessionLocal
import requests
import time
import json

MAX_RETRIES = 5
TIMEOUT_SECONDS = 5

@celery_app.task(bind=True, max_retries=MAX_RETRIES)
def process_webhook_delivery(self, subscription_id: int, payload: dict, event_type: str = None, attempt_number: int = 1):
    """Process webhook delivery with retry logic"""
    db = SessionLocal()
    try:
        # Get subscription with caching
        subscription = services.get_subscription_with_cache(db, subscription_id)
        if not subscription:
            raise Exception(f"Subscription {subscription_id} not found.")

        headers = {"Content-Type": "application/json"}
        response = requests.post(subscription.target_url, data=json.dumps(payload), headers=headers, timeout=TIMEOUT_SECONDS)

        delivery_data = {
            "task_id": self.request.id,
            "subscription_id": subscription_id,
            "target_url": subscription.target_url,
            "payload": payload,
            "attempt_number": attempt_number,
            "status": "Success" if 200 <= response.status_code < 300 else "Failed Attempt",
            "status_code": response.status_code,
            "error_message": None if 200 <= response.status_code < 300 else f"Received status code {response.status_code}"
        }
        services.log_delivery(db, delivery_data)

        if not (200 <= response.status_code < 300):
            raise Exception(f"Failed with status {response.status_code}")

    except Exception as exc:
        services.log_delivery(db, {
            "task_id": self.request.id,
            "subscription_id": subscription_id,
            "target_url": subscription.target_url if subscription else '',
            "payload": payload,
            "attempt_number": attempt_number,
            "status": "Failed Attempt",
            "status_code": None,
            "error_message": str(exc),
        })
        delay = 2 ** attempt_number
        if attempt_number < MAX_RETRIES:
            raise self.retry(exc=exc, countdown=delay)
        else:
            services.log_delivery(db, {
                "task_id": self.request.id,
                "subscription_id": subscription_id,
                "target_url": subscription.target_url if subscription else '',
                "payload": payload,
                "attempt_number": attempt_number,
                "status": "Failure",
                "status_code": None,
                "error_message": f"Max retries reached: {str(exc)}",
            })
    finally:
        db.close()

def queue_webhook_delivery(subscription_id: int, payload: dict, event_type: str = None):
    """Queue a webhook for delivery"""
    result = process_webhook_delivery.delay(subscription_id=subscription_id, payload=payload, event_type=event_type)
    return result.id 