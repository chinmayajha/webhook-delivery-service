from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict
from datetime import datetime
from .config import Base

# SQLAlchemy Models
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False)
    secret = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, nullable=False)
    subscription_id = Column(Integer, nullable=False)
    target_url = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    attempt_number = Column(Integer, default=1)
    status = Column(String, nullable=False)  # Success, Failed Attempt, or Failure
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic Schemas
class SubscriptionBase(BaseModel):
    target_url: HttpUrl
    secret: Optional[str] = None
    event_type: Optional[str] = None

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(SubscriptionBase):
    pass

class SubscriptionOut(SubscriptionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class DeliveryLogOut(BaseModel):
    id: int
    task_id: str
    subscription_id: int
    target_url: str
    attempt_number: int
    status: str
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime

    class Config:
        orm_mode = True 