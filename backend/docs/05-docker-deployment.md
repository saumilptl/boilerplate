# Docker & Deployment

## Overview

The application uses multi-stage Docker builds with separate containers for:
- **API** - FastAPI web server with Uvicorn
- **Worker** - Celery task worker with hot-reload
- **PostgreSQL** - Database (postgres:16-alpine)
- **Redis** - Cache and message broker (redis:7-alpine)

## Docker Architecture

### Multi-Stage Dockerfile

```dockerfile
# Stage 1: base - System dependencies and EJSON CLI
# Stage 2: dependencies - Python packages installed via Poetry
# Stage 3: development - Development environment (used by docker-compose)
# Stage 4: build - Production build preparation
# Stage 5: api - Production API server
# Stage 6: worker - Production Celery worker
```

**Benefits:**
- Development environment with hot-reload and volume mounts
- Smaller production images
- Faster builds with layer caching
- Separate API and worker images from same source

### Container Structure

```
backend-api       ← FastAPI + Uvicorn (development target with --reload)
backend-worker    ← Celery worker (development target with --reload)
backend-postgres  ← PostgreSQL 16
backend-redis     ← Redis 7
```

## Quick Start

### Development

```bash
# Start all services
docker compose up

# Build and start
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f api worker

# Stop all
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Accessing Services

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5433 (mapped from container port 5432)
- Redis: localhost:6379

## Data Persistence

All Docker data is stored in the gitignored `dockerdata/` folder:

```
dockerdata/
├── postgres-data/     # PostgreSQL database files
├── redis-data/        # Redis append-only file
└── poetry-cache/      # Poetry package cache (speeds up rebuilds)
```

**Why dockerdata/?**
- Keeps all Docker-related data in one place
- Easy to backup/restore entire development state
- gitignored to prevent committing large binary files
- Persists between container restarts
- Can be safely deleted to start fresh

```bash
# Remove all Docker data (fresh start)
rm -rf dockerdata/

# Backup data
tar -czf backup.tar.gz dockerdata/

# Restore data
tar -xzf backup.tar.gz
```

## EJSON Secrets Management

### How It Works

1. **Host Setup:**
   - EJSON keys exist in `ejson-keys/` directory (gitignored)
   - `secrets/development.json` contains configuration
   - Encrypted to `secrets/development.ejson` (can be committed)

2. **Docker Setup:**
   - Containers receive `EJSON_PUBLIC_KEY` and `EJSON_PRIVATE_KEY` as environment variables
   - Entrypoint runs `setup-ejson` to write keys to `/app/src/ejson-keys/`
   - Then runs `load-env` to decrypt secrets from `development.ejson`
   - `local.json` overrides are merged for additional customization

3. **Environment-Specific Configuration:**
   ```json
   // secrets/development.json (before encryption)
   {
     "_public_key": "6256...",
     "DATABASE": {
       "_HOST": "postgres",      // Docker container name
       "_PORT": 5432,            // Internal container port
       "USER": "app",
       "PASSWORD": "app_password"
     },
     "REDIS": {
       "_HOST": "redis",         // Docker container name
       "_PORT": 6379,
       "PASSWORD": "redis_password"
     }
   }
   ```

4. **Local Development Overrides (secrets/local.json):**
   ```json
   {
     "DATABASE": {
       "_HOST": "localhost",   // Override for host development
       "_PORT": 5433           // External port
     },
     "REDIS": {
       "_HOST": "localhost"
     }
   }
   ```

   The `local.json` file is merged with EJSON secrets, allowing you to override specific values without re-encrypting. In Docker, the EJSON values are used directly. On the host, local.json overrides the database/redis hosts to localhost.

### Managing EJSON Keys

```bash
# Read public key
cat ejson-keys/*

# Example output: 6256bbbb216566dd58f2469d75e480b04793191064ab19c5cb8046c012a1fc25

# These keys are passed to Docker containers as environment variables
# See docker-compose.yaml environment section
```

## Configuration

### docker-compose.yaml Structure

```yaml
services:
  postgres:
    image: postgres:16-alpine
    volumes:
      - ./dockerdata/postgres-data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # External:Internal

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass redis_password
    volumes:
      - ./dockerdata/redis-data:/data
    ports:
      - "6379:6379"

  api:
    build:
      context: .
      target: development  # Use development stage
    working_dir: /app/src
    volumes:
      - .:/app/src  # Mount source for hot-reload
      - ./dockerdata/poetry-cache:/root/.cache/pypoetry
    environment:
      - ENVIRONMENT=development
      - EJSON_PUBLIC_KEY=6256bbbb...
      - EJSON_PRIVATE_KEY=02656c16...
      - PYTHONUNBUFFERED=1
    entrypoint: ["sh", "-c"]
    command: ["./scripts/docker/api.entrypoint.sh"]

  worker:
    build:
      context: .
      target: development
    working_dir: /app/src
    volumes:
      - .:/app/src
      - ./dockerdata/poetry-cache:/root/.cache/pypoetry
    environment:
      - ENVIRONMENT=development
      - EJSON_PUBLIC_KEY=6256bbbb...
      - EJSON_PRIVATE_KEY=02656c16...
      - RUN_CELERY_BEAT=true
    entrypoint: ["sh", "-c"]
    command: ["./scripts/docker/worker.entrypoint.sh"]
```

## Entrypoint Scripts

### API Entrypoint (`scripts/docker/api.entrypoint.sh`)

```bash
#!/bin/bash
source "$(dirname "$0")/common.entrypoint.sh"

# Load secrets (setup-ejson + load-env)
load_secrets

# Source .env.tmp if it exists (ENV_ prefixed vars)
setup_environment

# Run migrations
poetry run poe migration-upgrade

# Start API server
if [ "$ENVIRONMENT" == "development" ]; then
    poetry run poe serve api --reload  # Hot-reload enabled
else
    poetry run poe serve api
fi
```

### Worker Entrypoint (`scripts/docker/worker.entrypoint.sh`)

```bash
#!/bin/bash
source "$(dirname "$0")/common.entrypoint.sh"

load_secrets
setup_environment

beat_flag=""
if [ "$RUN_CELERY_BEAT" == "true" ]; then
    beat_flag="--beat"
fi

if [ "$ENVIRONMENT" == "development" ]; then
    poetry run poe serve worker $beat_flag --reload  # Hot-reload enabled
else
    poetry run poe serve worker $beat_flag
fi
```

### Common Entrypoint (`scripts/docker/common.entrypoint.sh`)

```bash
#!/bin/bash
source "$(dirname "$0")/../../env_constants.sh"

# Install dependencies in development mode
if [ "$ENVIRONMENT" == "development" ]; then
    echo "Development environment detected. Installing package from mounted source..."
    cd /app/src && poetry install
    cd - > /dev/null
fi

load_secrets() {
    local force_flag=""
    if [ "$1" == "-f" ]; then
        force_flag="--force"
    fi

    poetry run setup-ejson && poetry run load-env $force_flag

    if [ $? -ne 0 ]; then
        echo "Failed to load secrets. Exiting."
        exit 1
    fi
}

setup_environment() {
    if [ -f "$TMP_ENV_PATH" ]; then
        set -a
        source "$TMP_ENV_PATH"
        set +a
        shred -u "$TMP_ENV_PATH"
    fi
}
```

## Hot-Reload

Both API and Worker support hot-reload in development:

### API Hot-Reload
- Uses `uvicorn --reload`
- Watches Python files for changes
- Automatically restarts on file modification
- Preserves database connections

### Worker Hot-Reload
- Uses `watchmedo` (watchdog package)
- Monitors task files for changes
- Restarts Celery worker on changes
- Maintains queue connections

**Test hot-reload:**
```bash
# Edit a file
echo "# Test comment" >> app/api/routes/health.py

# Watch logs
docker compose logs -f api worker

# Should see reload messages
```

## Health Checks

### PostgreSQL

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U app -d app_db"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

### Redis

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 5s
```

### API

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**Test manually:**
```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "1.0.0"}

curl http://localhost:8000/api/health/ready
# {"status": "ready", "database": "connected"}
```

### Worker

```yaml
healthcheck:
  test: ["CMD", "celery", "-A", "app.worker.app", "inspect", "ping", "-d", "celery@worker"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

## Container Commands

### API Container

```bash
# Shell access
docker compose exec api bash

# Run migrations
docker compose exec api poetry run poe migration-upgrade

# Check routes
docker compose exec api poetry run python -c "from app.api.app import create_app; app = create_app(); print([r.path for r in app.routes])"

# Check logs
docker compose logs api -f --tail=100

# Restart
docker compose restart api
```

### Worker Container

```bash
# View active tasks
docker compose exec worker poetry run celery -A app.worker.app inspect active

# View registered tasks
docker compose exec worker poetry run celery -A app.worker.app inspect registered

# Purge queue
docker compose exec worker poetry run celery -A app.worker.app purge

# Worker stats
docker compose exec worker poetry run celery -A app.worker.app inspect stats

# Restart
docker compose restart worker
```

### Database

```bash
# PostgreSQL shell
docker compose exec postgres psql -U app -d app_db

# Run query
docker compose exec postgres psql -U app -d app_db -c "SELECT * FROM users;"

# Backup
docker compose exec postgres pg_dump -U app app_db > backup.sql

# Restore
cat backup.sql | docker compose exec -T postgres psql -U app -d app_db

# View tables
docker compose exec postgres psql -U app -d app_db -c "\dt"
```

### Redis

```bash
# Redis CLI
docker compose exec redis redis-cli -a redis_password

# Monitor commands
docker compose exec redis redis-cli -a redis_password MONITOR

# View keys
docker compose exec redis redis-cli -a redis_password KEYS '*'

# Flush all
docker compose exec redis redis-cli -a redis_password FLUSHALL
```

## Troubleshooting

### Container Won't Start

```bash
# Check container status
docker compose ps

# View logs
docker compose logs api

# Check specific error
docker compose logs api --tail=50

# Rebuild without cache
docker compose build --no-cache api

# Remove everything and start fresh
docker compose down -v
rm -rf dockerdata/
docker compose up --build
```

### EJSON Key Issues

```bash
# Error: "Both EJSON_PUBLIC_KEY and EJSON_PRIVATE_KEY are required"

# Solution: Check docker-compose.yaml has the keys
grep EJSON docker-compose.yaml

# Should see:
# - EJSON_PUBLIC_KEY=6256bbbb...
# - EJSON_PRIVATE_KEY=02656c16...
```

### Database Connection Issues

```bash
# Check if postgres is healthy
docker compose ps postgres

# Test connection from API
docker compose exec api poetry run python -c "
from app.config import config
from app.infra.database.db import get_database
cfg = config()
print(f'DB: {cfg.DATABASE.HOST}:{cfg.DATABASE.PORT}')
"

# Should print: DB: postgres:5432
```

### Hot-Reload Not Working

```bash
# Check if volumes are mounted
docker compose exec api ls -la /app/src/app/

# Should see your source files, not copied files

# Check if watchdog is installed
docker compose exec worker poetry show watchdog

# Restart with fresh build
docker compose down
docker compose up --build
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yaml
ports:
  - "8001:8000"
```

### Permission Issues (Linux)

```bash
# If dockerdata folders have wrong permissions

# Fix ownership
sudo chown -R $USER:$USER dockerdata/

# Or run as root in container (not recommended for production)
docker compose exec -u root api bash
```

## Production Deployment

### Building Production Images

```bash
# Build production API image
docker build --target api -t myapp/api:latest .

# Build production worker image
docker build --target worker -t myapp/worker:latest .

# Tag with version
docker tag myapp/api:latest myapp/api:v1.0.0

# Push to registry
docker push myapp/api:v1.0.0
```

### Production docker-compose.yaml

```yaml
services:
  api:
    image: myapp/api:v1.0.0
    restart: always
    environment:
      - ENVIRONMENT=production
      - EJSON_PUBLIC_KEY=${EJSON_PUBLIC_KEY}
      - EJSON_PRIVATE_KEY=${EJSON_PRIVATE_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
    # No volume mounts in production
```

### Environment Variables

**Required:**
- `ENVIRONMENT=production`
- `EJSON_PUBLIC_KEY` - Public EJSON key
- `EJSON_PRIVATE_KEY` - Private EJSON key (from secrets manager)

**Optional overrides (if not in EJSON):**
- `DATABASE__HOST` - Database hostname
- `DATABASE__PORT` - Database port
- `REDIS__HOST` - Redis hostname
- `REDIS__PORT` - Redis port

### Secrets Management in Production

**Option 1: Environment Variables (AWS ECS/Fargate)**
```bash
aws ecs run-task \
  --task-definition myapp \
  --overrides '{
    "containerOverrides": [{
      "name": "api",
      "environment": [
        {"name": "EJSON_PRIVATE_KEY", "value": "..."}
      ]
    }]
  }'
```

**Option 2: Secrets Manager (AWS ECS)**
```json
{
  "secrets": [
    {
      "name": "EJSON_PRIVATE_KEY",
      "valueFrom": "arn:aws:secretsmanager:region:account:secret:ejson-key"
    }
  ]
}
```

**Option 3: Kubernetes Secrets**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ejson-keys
type: Opaque
data:
  public-key: NjI1NmJiYmI...  # base64 encoded
  private-key: MDI2NTZjMTY...  # base64 encoded
```

## Monitoring

### Container Metrics

```bash
# Resource usage
docker stats

# Specific containers
docker stats backend-api backend-worker

# JSON format
docker stats --no-stream --format "{{json .}}"
```

### Application Logs

```bash
# Follow logs
docker compose logs -f

# Specific services
docker compose logs -f api worker

# Last N lines
docker compose logs --tail=100 api

# With timestamps
docker compose logs -t api

# Filter by level
docker compose logs api | grep ERROR
docker compose logs api | grep INFO
```

### Health Status

```bash
# Check all services
docker compose ps

# API health
curl http://localhost:8000/api/health

# Database health
curl http://localhost:8000/api/health/ready
```

## Performance Optimization

### Build Cache

The Dockerfile is optimized for layer caching:

```dockerfile
# Dependencies layer (rarely changes)
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Source code layer (changes frequently)
COPY . .
RUN poetry install
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Network Optimization

- All containers on same network (no NAT overhead)
- Health checks prevent traffic to unhealthy containers
- Connection pooling in application layer

## Security Best Practices

1. **Never commit secrets:**
   - `ejson-keys/` is gitignored
   - `secrets/*.json` are gitignored
   - Only commit encrypted `secrets/*.ejson`

2. **Use specific image versions:**
   ```dockerfile
   FROM python:3.12-slim  # Not 'latest'
   ```

3. **Scan images:**
   ```bash
   docker scan myapp/api:latest
   ```

4. **Minimize attack surface:**
   - Multi-stage builds keep production images small
   - Only production dependencies in final image
   - No dev tools or source maps

5. **Rotate secrets regularly:**
   ```bash
   # Generate new EJSON keypair
   ejson keygen

   # Update secrets/development.ejson with new key
   # Re-encrypt
   poetry run encrypt-ejson development
   ```
