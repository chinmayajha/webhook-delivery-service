from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import json
from . import models
from .config import redis_client

# Cache configuration
SUBSCRIPTION_CACHE_PREFIX = "subscription:"
CACHE_EXPIRY = 3600  # 1 hour

# Subscription Services
def create_subscription_record(db: Session, subscription: models.SubscriptionCreate):
    """Create a new webhook subscription"""
    db_subscription = models.Subscription(**subscription.dict())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def get_subscription_by_id(db: Session, subscription_id: int):
    """Get subscription by ID"""
    return db.query(models.Subscription).filter(models.Subscription.id == subscription_id).first()

def update_subscription_record(db: Session, subscription_id: int, subscription: models.SubscriptionUpdate):
    """Update an existing subscription"""
    db_subscription = get_subscription_by_id(db, subscription_id)
    if not db_subscription:
        return None
    for var, value in vars(subscription).items():
        setattr(db_subscription, var, value) if value else None
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def delete_subscription_record(db: Session, subscription_id: int):
    """Delete a subscription"""
    db_subscription = get_subscription_by_id(db, subscription_id)
    if db_subscription:
        db.delete(db_subscription)
        db.commit()

# Cache Services
def fetch_cached_subscription(subscription_id: int) -> Optional[models.SubscriptionOut]:
    """Get subscription from cache"""
    key = f"{SUBSCRIPTION_CACHE_PREFIX}{subscription_id}"
    cached = redis_client.get(key)
    if cached:
        data = json.loads(cached)
        return models.SubscriptionOut(**data)
    return None

def cache_subscription_data(subscription):
    """Cache subscription data"""
    key = f"{SUBSCRIPTION_CACHE_PREFIX}{subscription.id}"
    data = {
        "id": subscription.id,
        "target_url": subscription.target_url,
        "secret": subscription.secret,
        "event_type": subscription.event_type,
        "created_at": str(subscription.created_at)
    }
    redis_client.set(key, json.dumps(data), ex=CACHE_EXPIRY)

def get_subscription_with_cache(db: Session, subscription_id: int):
    """Get subscription with caching"""
    # Try cache first
    cached = fetch_cached_subscription(subscription_id)
    if cached:
        return cached
    
    # Fallback to database
    db_subscription = get_subscription_by_id(db, subscription_id)
    if db_subscription:
        cache_subscription_data(db_subscription)
    return db_subscription

# Delivery Services
def log_delivery(db: Session, delivery_data: dict):
    """Log a delivery attempt"""
    db_log = models.DeliveryLog(**delivery_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_delivery_by_task_id(db: Session, task_id: str):
    """Get delivery status by task ID"""
    return db.query(models.DeliveryLog).filter(models.DeliveryLog.task_id == task_id).order_by(desc(models.DeliveryLog.attempt_number)).first()

def get_recent_deliveries(db: Session, subscription_id: int) -> List[models.DeliveryLog]:
    """Get recent deliveries for a subscription"""
    return db.query(models.DeliveryLog).filter(models.DeliveryLog.subscription_id == subscription_id).order_by(desc(models.DeliveryLog.timestamp)).limit(20).all()

def cleanup_old_logs(db: Session, hours: int = 72):
    """Clean up old delivery logs"""
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    db.query(models.DeliveryLog).filter(models.DeliveryLog.timestamp < cutoff).delete()
    db.commit() 