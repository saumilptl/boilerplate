# Configuration & Secrets Management

## Overview

Configuration is managed through EJSON encrypted secrets with a hierarchical loading system:
1. **EJSON files** - Encrypted environment-specific secrets (`.ejson` files)
2. **Decrypted secrets** - Automatically decrypted `.json` files (gitignored)
3. **local.json** - Local development overrides (gitignored, dev only)
4. **Environment variable overrides** - Optional runtime overrides

## Configuration Loading Order

```
1. Decrypt {environment}.ejson to {environment}.json (using ejson-keys/)
2. Load decrypted secrets and strip _ and ENV_ prefixes
3. Merge local.json with deep merge (development only)
4. Apply environment variable overrides (when force=False)
```

Later sources override earlier ones.

## EJSON Encrypted Secrets

### EJSON Prefix Conventions

EJSON uses prefixes to distinguish between encrypted and unencrypted values:

- **`_` prefix** = Unencrypted (non-sensitive): `_HOST`, `_PORT`, `_DEBUG`
- **No prefix** = Encrypted (sensitive): `USER`, `PASSWORD`, `JWT_SECRET_KEY`
- **`ENV_` prefix** = Environment variable (with `_` if unencrypted): `_ENV_DEBUG`

Prefixes are automatically stripped during loading, so `_HOST` becomes `HOST` in your config.

### Setup

```bash
# Generate EJSON keypair
ejson keygen

# This outputs:
# Public Key:  abc123...
# Private Key: def456...

# Set up keys using environment variables
export EJSON_PUBLIC_KEY="abc123..."
export EJSON_PRIVATE_KEY="def456..."
poetry run setup-ejson

# This creates ejson-keys/{public_key} with the private key
# Keys are stored in ./ejson-keys/ (gitignored - NEVER COMMIT)
```

### File Structure

**secrets/development.json** (unencrypted source, gitignored):
```json
{
  "_public_key": "abc123...",
  "_ENVIRONMENT": "development",
  "_SERVICE_NAME": "backend-api",
  "_DEBUG": true,
  "DATABASE": {
    "_HOST": "localhost",
    "_PORT": 5433,
    "_NAME": "app_db",
    "USER": "app",
    "PASSWORD": "app_password"
  },
  "SECURITY": {
    "JWT_SECRET_KEY": "your-secret-key"
  }
}
```

**secrets/development.ejson** (encrypted, committed to git):
```json
{
  "_public_key": "abc123...",
  "_ENVIRONMENT": "development",
  "_SERVICE_NAME": "backend-api",
  "_DEBUG": true,
  "DATABASE": {
    "_HOST": "localhost",
    "_PORT": 5433,
    "_NAME": "app_db",
    "USER": "EJ[1:encrypted_value...]",
    "PASSWORD": "EJ[1:encrypted_value...]"
  },
  "SECURITY": {
    "JWT_SECRET_KEY": "EJ[1:encrypted_value...]"
  }
}
```

### Encryption Workflow

```bash
# 1. Create/edit the unencrypted .json file
vim secrets/production.json

# 2. Encrypt it to create .ejson file
poetry run encrypt-ejson production

# This creates secrets/production.ejson (encrypted)
# And renames the .json file to .ejson

# 3. Commit the .ejson file
git add secrets/production.ejson
git commit -m "Update production secrets"
```

### Decryption

Decryption happens automatically during application startup:

```bash
# Application automatically:
# 1. Checks if secrets/{environment}.json exists
# 2. If not, runs: ejson decrypt secrets/{environment}.ejson -o secrets/{environment}.json
# 3. Loads the decrypted secrets
# 4. Strips _ and ENV_ prefixes from keys
```

Manual decryption for debugging:
```bash
poetry run decrypt-ejson development
# Creates secrets/development.json from secrets/development.ejson
```

## Local Development Overrides

**secrets/local.json** (gitignored, only loaded in development):
```json
{
  "_ENVIRONMENT": "development",
  "_DEBUG": true,
  "DATABASE": {
    "_HOST": "localhost",
    "_PORT": 5433,
    "USER": "myuser",
    "PASSWORD": "mypassword"
  }
}
```

**Important:** Use `_` prefix for unencrypted values, no prefix for sensitive values.

The deep merge strategy means you can override just specific values:
```json
{
  "DATABASE": {
    "_PORT": 5434  // Only override port, keep other DATABASE settings
  }
}
```

## Environment Variable Overrides

Environment variables can override secrets when `force=False` (the default):

```python
# In SecretsLoader initialization
SecretsLoader(env=Environment.DEVELOPMENT, force=False)
# force=False: env vars override secrets
# force=True: secrets override env vars
```

The override uses the stripped key names:
```bash
# To override DATABASE.HOST
export HOST=custom-host

# To override DATABASE.PORT
export PORT=5434
```

## Configuration Schema

### Main Configuration

```python
class Config:
    ENVIRONMENT: Environment      # development, staging, production
    SERVICE_NAME: str            # Service name for monitoring
    DEBUG: bool                  # Debug mode
    HOST: str                    # Server host
    PORT: int                    # Server port
    WORKERS: int                 # Number of workers
    RELOAD: bool                 # Enable auto-reload
```

### Database Configuration
```python
class DatabaseConfig:
    HOST: str              # Database hostname
    PORT: int              # Database port
    USER: str              # Database user
    PASSWORD: str          # Database password
    NAME: str              # Database name
    DRIVER: str            # SQLAlchemy driver (postgresql+asyncpg)
    SSL_MODE: str          # SSL mode (prefer, require, disable)
    POOL_SIZE: int         # Connection pool size
    MAX_OVERFLOW: int      # Max overflow connections
    POOL_RECYCLE: int      # Connection recycle time (seconds)
    POOL_PRE_PING: bool    # Pre-ping before using connection
    ECHO: bool             # Echo SQL queries (debug only)
```

### Redis Configuration
```python
class RedisConfig:
    HOST: str              # Redis hostname
    PORT: int              # Redis port
    DB: int                # Redis database number
    PASSWORD: str | None   # Redis password
    SSL_MODE: bool         # Enable SSL
    MAX_CONNECTIONS: int   # Max connections
```

### Security Configuration
```python
class SecurityConfig:
    JWT_SECRET_KEY: str                    # JWT signing key
    JWT_ALGORITHM: str                     # JWT algorithm (HS256)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int   # Token expiration
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int     # Refresh token expiration
    PASSWORD_MIN_LENGTH: int               # Min password length
    PASSWORD_REQUIRE_UPPERCASE: bool       # Require uppercase
    PASSWORD_REQUIRE_LOWERCASE: bool       # Require lowercase
    PASSWORD_REQUIRE_DIGIT: bool           # Require digit
    PASSWORD_REQUIRE_SPECIAL: bool         # Require special char
    RATE_LIMIT_ENABLED: bool               # Enable rate limiting
    RATE_LIMIT_PER_MINUTE: int             # Requests per minute
    CORS_ORIGINS: list[str]                # Allowed CORS origins
    CORS_ALLOW_CREDENTIALS: bool           # Allow credentials
```

### Monitoring Configuration
```python
class MonitoringConfig:
    DD_ENABLED: bool           # Enable Datadog
    DD_API_KEY: str | None     # Datadog API key
    DD_SITE: str               # Datadog site
    DD_APM_ENABLED: bool       # Enable APM
    DD_LOGS_ENABLED: bool      # Enable log collection
    OTEL_ENABLED: bool         # Enable OpenTelemetry
    OTEL_ENDPOINT: str | None  # OTEL collector endpoint
    OTEL_SAMPLING_RATE: float  # Trace sampling rate
    LOG_LEVEL: str             # Logging level
    LOG_JSON: bool             # JSON formatted logs
```

### Worker Configuration
```python
class WorkerConfig:
    TASK_RETRY_MAX_ATTEMPTS: int       # Max retry attempts
    TASK_RETRY_BACKOFF: int            # Retry backoff (seconds)
    TASK_SOFT_TIME_LIMIT: int          # Soft time limit
    TASK_TIME_LIMIT: int               # Hard time limit
    WORKER_PREFETCH_MULTIPLIER: int    # Prefetch multiplier
    WORKER_MAX_TASKS_PER_CHILD: int    # Max tasks per worker
    WORKER_AUTOSCALE_MIN: int          # Min workers
    WORKER_AUTOSCALE_MAX: int          # Max workers
    ENABLE_BEAT: bool                  # Enable beat scheduler
```

## Accessing Configuration

### In Application Code

```python
from app.config import config

cfg = config()

# Access nested config
db_host = cfg.DATABASE.HOST
jwt_secret = cfg.SECURITY.JWT_SECRET_KEY

# Database URLs
async_url = cfg.DATABASE.url       # postgresql+asyncpg://...
sync_url = cfg.DATABASE.sync_url   # postgresql://... (for Alembic)

# Redis URL
redis_url = cfg.REDIS.url          # redis://... or rediss://...
```

### In Scripts

```python
from app.config import config

cfg = config()
print(f"Connecting to {cfg.DATABASE.HOST}:{cfg.DATABASE.PORT}")
```

## Management Commands

```bash
# Setup EJSON keys from environment variables
export EJSON_PUBLIC_KEY="your-public-key"
export EJSON_PRIVATE_KEY="your-private-key"
poetry run setup-ejson

# Encrypt secrets
poetry run encrypt-ejson development    # Creates development.ejson from development.json
poetry run encrypt-ejson production

# Decrypt secrets (for debugging)
poetry run decrypt-ejson development    # Creates development.json from development.ejson
poetry run decrypt-ejson production
```

## Best Practices

### 1. Never Commit Secrets

The `.gitignore` includes:
```
secrets/*.json       # Decrypted files
secrets/*.key        # Old-style key files
ejson-keys/          # Private keys directory
```

Only commit:
- `secrets/*.ejson` (encrypted files)
- `secrets/local.json.example` (example template)

### 2. Use Prefixes Correctly

```json
{
  "_DEBUG": true,              // Unencrypted - safe to see
  "_HOST": "localhost",        // Unencrypted - non-sensitive
  "_PORT": 5433,               // Unencrypted - non-sensitive
  "PASSWORD": "secret123",     // Will be encrypted - sensitive
  "JWT_SECRET_KEY": "secret"   // Will be encrypted - sensitive
}
```

### 3. Encryption Workflow

```bash
# 1. Edit the unencrypted file
vim secrets/production.json

# 2. Encrypt it
poetry run encrypt-ejson production

# 3. Commit only the .ejson
git add secrets/production.ejson
git commit -m "Update production secrets"

# Never commit the .json file!
```

### 4. Share Private Keys Securely

- Use 1Password, AWS Secrets Manager, or similar
- Never commit to git
- Never send via email/Slack
- Store in CI/CD secrets for automated deployments

### 5. Local Development

```bash
# Copy example to start
cp secrets/local.json.example secrets/local.json

# Edit with your local settings
vim secrets/local.json

# Remember: use _ prefix for unencrypted values
```

## Environment-Specific Setup

### Development

```bash
export ENVIRONMENT=development
# Uses: development.ejson → development.json + local.json + env overrides
```

### Staging

```bash
export ENVIRONMENT=staging
# Uses: staging.ejson → staging.json + env overrides
# (no local.json in non-development environments)
```

### Production

```bash
export ENVIRONMENT=production
# Uses: production.ejson → production.json + env overrides
```

## Docker Configuration

### EJSON in Docker

Containers receive EJSON keys as environment variables and use entrypoint scripts to set them up:

```yaml
services:
  api:
    build:
      target: development  # Or 'api' for production
    working_dir: /app/src
    volumes:
      - .:/app/src  # Development only: mount source for hot-reload
      - ./dockerdata/poetry-cache:/root/.cache/pypoetry
    environment:
      - ENVIRONMENT=development
      - SERVICE_NAME=backend-api
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - EJSON_PUBLIC_KEY=6256bbbb216566dd58f2469d75e480b04793191064ab19c5cb8046c012a1fc25
      - EJSON_PRIVATE_KEY=02656c1694ded4f36048115b53f4b32087a817b3339e3fe1c025b6a312313dee
    entrypoint: ["sh", "-c"]
    command: ["./scripts/docker/api.entrypoint.sh"]
```

### Entrypoint Flow

The `api.entrypoint.sh` and `worker.entrypoint.sh` scripts:

1. Run `poetry run setup-ejson` - Writes keys from env vars to `ejson-keys/` directory
2. Run `poetry run load-env` - Decrypts `development.ejson` and loads secrets
3. Merge `local.json` if it exists (for local overrides)
4. Start the service

```bash
#!/bin/bash
source "$(dirname "$0")/common.entrypoint.sh"

# Load secrets
load_secrets
setup_environment

# Run migrations (API only)
poetry run poe migration-upgrade

# Start service
poetry run poe serve api --reload
```

### Docker-Specific Configuration

**Important:** Container configuration differs from host development:

**In `secrets/development.json` (before encryption):**
```json
{
  "_public_key": "6256bbbb...",
  "DATABASE": {
    "_HOST": "postgres",  // Docker service name, not localhost
    "_PORT": 5432,        // Internal container port
    "USER": "app",
    "PASSWORD": "app_password"
  },
  "REDIS": {
    "_HOST": "redis",     // Docker service name
    "_PORT": 6379,
    "PASSWORD": "redis_password"
  }
}
```

**In `secrets/local.json` (for host development):**
```json
{
  "DATABASE": {
    "_HOST": "localhost",  // Override for host development
    "_PORT": 5433          // External mapped port
  },
  "REDIS": {
    "_HOST": "localhost"
  },
  "SECURITY": {
    "JWT_SECRET_KEY": "dev-secret-key"
  }
}
```

The `local.json` file is merged in both environments but **should not override infrastructure hosts** in Docker. Keep database/redis overrides minimal or remove them when running in Docker.

### Data Persistence

All Docker data is stored in the gitignored `dockerdata/` folder:

```
dockerdata/
├── postgres-data/     # PostgreSQL data files
├── redis-data/        # Redis persistence
└── poetry-cache/      # Poetry package cache
```

This is configured in docker-compose.yaml:
```yaml
volumes:
  - ./dockerdata/postgres-data:/var/lib/postgresql/data
  - ./dockerdata/redis-data:/data
  - ./dockerdata/poetry-cache:/root/.cache/pypoetry
```

### Networking

Containers communicate using service names as hostnames:
- `postgres` → PostgreSQL container (internal port 5432, external 5433)
- `redis` → Redis container (port 6379)
- `api` → API container (port 8000)
- `worker` → Worker container

**From host machine:** Use `localhost:5433` (external ports)
**From containers:** Use `postgres:5432` (internal ports)

## Troubleshooting

### Private Key Not Found

```
Error: couldn't read key file
```

**Solution:**
```bash
# Check if key exists
ls ejson-keys/

# If missing, run setup
export EJSON_PUBLIC_KEY="..."
export EJSON_PRIVATE_KEY="..."
poetry run setup-ejson
```

### Configuration Not Loading

1. Check environment variable:
   ```bash
   echo $ENVIRONMENT
   ```

2. Verify EJSON file exists:
   ```bash
   ls secrets/$ENVIRONMENT.ejson
   ```

3. Check private key:
   ```bash
   ls ejson-keys/
   ```

4. Test decryption manually:
   ```bash
   poetry run decrypt-ejson $ENVIRONMENT
   cat secrets/$ENVIRONMENT.json
   ```

### Key Collision Errors

```
SecretKeyCollisionError: Key collision detected: 'HOST' and '_HOST' both map to 'HOST'
```

**Solution:** Don't mix prefixed and non-prefixed versions of the same key:
```json
{
  "DATABASE": {
    "_HOST": "localhost",  // ✅ Use this
    "HOST": "other"        // ❌ Remove this - collision!
  }
}
```

### Wrong Prefix in local.json

Make sure `local.json` uses the same prefix convention as EJSON files:
```json
{
  "_HOST": "localhost",    // ✅ Correct
  "HOST": "localhost"      // ❌ Wrong - will cause collision
}
```
