from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models, services, workers, utils
from .config import get_db, engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(title="Webhook Delivery Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Subscription Routes
@app.post("/subscriptions/", response_model=models.SubscriptionOut)
def create_webhook_subscription(subscription: models.SubscriptionCreate, db: Session = Depends(get_db)):
    """Create a new webhook subscription"""
    return services.create_subscription_record(db, subscription)

@app.get("/subscriptions/{subscription_id}", response_model=models.SubscriptionOut)
def get_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Get subscription details"""
    db_subscription = services.get_subscription_by_id(db, subscription_id)
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription

@app.put("/subscriptions/{subscription_id}", response_model=models.SubscriptionOut)
def update_webhook_subscription(subscription_id: int, subscription: models.SubscriptionUpdate, db: Session = Depends(get_db)):
    """Update an existing subscription"""
    result = services.update_subscription_record(db, subscription_id, subscription)
    if result is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return result

@app.delete("/subscriptions/{subscription_id}")
def delete_webhook_subscription(subscription_id: int, db: Session = Depends(get_db)):
    """Delete a subscription"""
    services.delete_subscription_record(db, subscription_id)
    return {"message": "Subscription deleted"}

# Webhook Routes
@app.post("/ingest/{subscription_id}")
def process_webhook(subscription_id: int, background_tasks: BackgroundTasks, payload: dict, db: Session = Depends(get_db), event_type: str = None):
    """Process and queue a webhook for delivery"""
    subscription = services.get_subscription_with_cache(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Validate signature if secret is provided
    if subscription.secret:
        utils.validate_webhook_signature(subscription.secret, payload)

    # Check event type if specified
    if subscription.event_type and subscription.event_type != event_type:
        raise HTTPException(status_code=400, detail="Event type mismatch")

    # Queue webhook for delivery
    task_id = workers.queue_webhook_delivery(subscription_id, payload, event_type)
    return {"message": "Webhook queued for delivery", "task_id": task_id}

# Delivery Status Routes
@app.get("/status/{task_id}")
def get_delivery_status(task_id: str, db: Session = Depends(get_db)):
    """Get delivery status by task ID"""
    return services.get_delivery_by_task_id(db, task_id)

@app.get("/subscriptions/{subscription_id}/deliveries", response_model=List[models.DeliveryLogOut])
def get_delivery_history(subscription_id: int, db: Session = Depends(get_db)):
    """Get delivery history for a subscription"""
    return services.get_recent_deliveries(db, subscription_id)

# System Routes
@app.get("/health")
def health_check():
    """System health check"""
    return utils.get_system_health()

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to API docs"""
    return RedirectResponse(url="/docs") 