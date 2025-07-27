from src.webhook_service.config import celery_app

# Import workers to register them with Celery
import src.webhook_service.workers

if __name__ == "__main__":
    celery_app.start()
