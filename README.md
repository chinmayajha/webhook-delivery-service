# Webhook Delivery Service

A reliable webhook delivery system with retry logic, status tracking, and signature verification.

## Features

- **Reliable Delivery**: Exponential backoff retry (5 attempts)
- **Status Tracking**: Real-time delivery logs and history
- **Security**: HMAC-SHA256 signature verification
- **Performance**: Redis caching, async processing
- **Monitoring**: Automatic cleanup, health checks
- **Scalable**: Docker containerized, production-ready

## Tech Stack

- **FastAPI** - Web framework with auto-docs
- **Celery** - Background task processing
- **Redis** - Message broker & cache
- **PostgreSQL** - Database storage
- **Docker** - Containerized deployment

## Quick Start

```bash
git clone <repository-url>
cd webhook-delivery-service
docker-compose up --build
```

Access API docs: `http://localhost:8000/docs`

## Usage

### Create Subscription
```bash
curl -X POST "http://localhost:8000/subscriptions/" \
-H "Content-Type: application/json" \
-d '{
  "target_url": "https://your-app.com/webhook",
  "secret": "your-secret",
  "event_type": "order.created"
}'
```

### Send Webhook
```bash
curl -X POST "http://localhost:8000/ingest/1" \
-H "Content-Type: application/json" \
-H "X-Event-Type: order.created" \
-d '{"body": "payload", "signature": "hmac"}'
```

### Check Status
```bash
curl -X GET "http://localhost:8000/status/{task_id}"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/subscriptions/` | Create subscription |
| `GET` | `/subscriptions/{id}` | Get subscription |
| `PUT` | `/subscriptions/{id}` | Update subscription |
| `DELETE` | `/subscriptions/{id}` | Delete subscription |
| `POST` | `/ingest/{id}` | Send webhook |
| `GET` | `/status/{task_id}` | Check delivery status |
| `GET` | `/subscriptions/{id}/deliveries` | View delivery history |

## Architecture

```
Client → FastAPI → Redis Queue → Celery Workers → Target Webhooks
                ↓
            PostgreSQL (logs)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/postgres` | Database connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |

## Development

```bash
# Run tests
docker-compose run api pytest

# Local development
docker-compose up db redis
uvicorn src.webhook_service:app --reload
celery -A src.webhook_service.config.celery_app worker --loglevel=info
```

## Deployment

### Render.com (Free Tier)
1. Connect GitHub repo
2. Choose Docker deployment
3. Set `DATABASE_URL` and `REDIS_URL`
4. Deploy

### Other Platforms
- AWS ECS
- Google Cloud Run
- DigitalOcean App Platform
- Heroku

## Use Cases

- **E-commerce**: Order updates, payment confirmations
- **SaaS**: User events, subscription changes
- **IoT**: Sensor data, device status

## Troubleshooting

- **Delivery fails**: Check target URL, secret key, status codes
- **High memory**: Monitor Redis, check stuck Celery tasks
- **Slow performance**: Scale workers, optimize database queries

