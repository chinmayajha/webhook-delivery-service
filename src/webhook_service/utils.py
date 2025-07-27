import hmac
import hashlib
import base64
from fastapi import HTTPException
from datetime import datetime, timedelta
from .config import SessionLocal
from . import services

def validate_webhook_signature(secret: str, payload: dict):
    """Validate HMAC SHA256 signature if secret is provided"""
    if not secret:
        return

    signature_header = payload.get('signature')
    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature in payload")

    body = payload.get('body')
    if body is None:
        raise HTTPException(status_code=400, detail="Missing body in payload")

    computed_signature = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature_header, computed_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

def cleanup_expired_logs(hours: int = 72):
    """Clean up expired delivery logs"""
    db = SessionLocal()
    try:
        services.cleanup_old_logs(db, hours)
    finally:
        db.close()

def get_system_health():
    """Get system health status"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Test Redis connection
        from .config import redis_client
        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    } 