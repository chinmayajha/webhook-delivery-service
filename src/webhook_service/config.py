from celery import Celery
import redis
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/postgres")

# Celery configuration
celery_app = Celery(
    "webhook_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Redis client for caching
redis_client = redis.Redis.from_url(REDIS_URL)

# Database configuration
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Settings:
    DATABASE_URL: str = DATABASE_URL
    REDIS_URL: str = REDIS_URL

settings = Settings()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 