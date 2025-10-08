# Getting Started

## Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Poetry 2.1.0+
- Docker & Docker Compose (for containerized deployment)

## Installation

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### 2. Database Setup

**Local PostgreSQL:**
```bash
# Create database
createdb app_db

# Or using psql
psql -U postgres -c "CREATE DATABASE app_db;"
```

**Docker PostgreSQL:**
```bash
docker compose up -d postgres
```

### 3. Configure Secrets

```bash
# Copy example configuration
cp secrets/local.json.example secrets/local.json

# Edit with your settings
# Key settings to update:
# - DATABASE.HOST, PORT, USER, PASSWORD, NAME
# - REDIS.HOST, PORT, PASSWORD
# - SECURITY.JWT_SECRET_KEY
```

**Local Development (`secrets/local.json`):**
```json
{
  "DATABASE": {
    "HOST": "localhost",
    "PORT": 5433,
    "USER": "app",
    "PASSWORD": "app_password",
    "NAME": "app_db"
  },
  "REDIS": {
    "HOST": "localhost",
    "PORT": 6379,
    "PASSWORD": "redis_password"
  },
  "SECURITY": {
    "JWT_SECRET_KEY": "your-secret-key-change-in-production"
  }
}
```

### 4. Run Migrations

```bash
# Apply database migrations
poetry run poe migration-upgrade

# Check migration status
poetry run poe migration-current
```

### 5. Start Development Server

**Option A: Local Python**
```bash
# Start API server
poetry run poe dev

# In another terminal, start worker
poetry run poe worker
```

**Option B: Docker**
```bash
# Start all services
docker compose up

# Or build and start
docker compose up --build
```

## Verify Installation

### Check API Health
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"healthy"}
```

### Check Documentation
Open browser: http://localhost:8000/docs

### Test User Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'
```

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/bearer/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=test@example.com&password=SecurePassword123!'
```

## Common Issues

### Database Connection Error
- Verify PostgreSQL is running: `pg_isready`
- Check connection settings in `secrets/local.json`
- Ensure database exists: `psql -l | grep app_db`

### Migration Errors
- Check current migration: `poetry run poe migration-current`
- Downgrade if needed: `poetry run poe migration-downgrade`
- Regenerate: `poetry run poe migration-generate "description"`

### Port Already in Use
- Change port in `secrets/local.json`: `"PORT": 8001`
- Or kill existing process: `lsof -ti:8000 | xargs kill -9`

## Next Steps

- Read [Configuration](./02-configuration.md) to understand secrets management
- Review [Authentication](./04-authentication.md) to customize auth
- See [Development](./06-development.md) for workflow best practices
