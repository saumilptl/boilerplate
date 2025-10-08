# Claude Development Guidelines

This document provides context for AI assistants working on this codebase.

## Project Overview

Production-ready FastAPI backend boilerplate with:
- FastAPI Users authentication (JWT bearer tokens)
- PostgreSQL + SQLModel ORM
- Alembic migrations
- Celery workers with Redis
- EJSON encrypted secrets management
- Docker multi-stage builds
- Repository pattern with dependency injection

## Critical Rules

### Configuration & Secrets

1. **NEVER commit secrets**
   - `secrets/*.json` (decrypted) are gitignored - use for local dev only
   - `secrets/*.ejson` are encrypted - these CAN be committed
   - `ejson-keys/` contains private keys - NEVER commit

2. **EJSON prefix conventions**
   - Use `_` prefix for unencrypted values (non-sensitive): `_HOST`, `_PORT`
   - No prefix for encrypted values (sensitive): `USER`, `PASSWORD`
   - Use `ENV_` prefix (with `_` for unencrypted) for environment variables: `_ENV_DEBUG`
   - The `_` and `ENV_` prefixes are automatically stripped during loading

3. **Configuration loading order**
   ```
   1. Decrypt {environment}.ejson to {environment}.json
   2. Load decrypted secrets and strip prefixes
   3. Merge local.json with deep merge (development only)
   4. Apply environment variable overrides when force=False
   ```
   Later sources override earlier ones.

4. **EJSON management commands**
   ```bash
   poetry run setup-ejson    # Setup EJSON keys from env vars
   poetry run encrypt-ejson development  # Encrypt .json to .ejson
   poetry run decrypt-ejson development  # Decrypt .ejson to .json
   ```

### Database & Migrations

1. **NEVER manually edit generated migrations**
   - If migration is wrong, downgrade and regenerate
   - Delete the migration file and run `poetry run poe migration-generate` again
   - Always review auto-generated migrations before applying

2. **Migration workflow**
   ```bash
   # Make model changes first
   # Then generate migration
   poetry run poe migration-generate "description"
   # Review the generated file in alembic/versions/
   # Apply migration
   poetry run poe migration-upgrade
   ```

3. **Model registration**
   - All models must be imported in `alembic/env.py`
   - Currently imports: `app.auth.models`
   - Add new modules here for migration auto-generation

4. **Base models available**
   - `BaseModel` - UUID primary key
   - `TimeStampedModel` - Adds created_at, updated_at
   - `AuditableModel` - Adds created_by_id, updated_by_id
   - `SoftDeleteModel` - Adds deleted_at, deleted_by_id

### Code Style & Quality

1. **Import organization**
   ```python
   # Standard library
   import os
   from typing import Optional

   # Third party
   from fastapi import APIRouter
   from sqlmodel import Field

   # Local
   from app.config import config
   ```

2. **Type hints required**
   - All function signatures must have type hints
   - Use `Optional[T]` or `T | None` for nullable types
   - Repository methods use Generic types
   - Always include return type annotations (including `-> None`)

3. **Naming conventions**
   - NEVER use "enhanced", "extended", "improved" in names
   - Be specific: `UserAuthenticationManager` not `EnhancedUserManager`
   - Use descriptive names that reflect purpose

4. **Documentation**
   - Docstrings for all public functions/classes
   - Use Google-style docstrings
   - Include Args, Returns, Raises sections

5. **Ruff linting standards**
   - Minimize use of `noqa` comments - fix issues properly when possible
   - Only use `noqa` for legitimate cases:
     - `ARG002`: Unused arguments required by parent class/interface (e.g., FastAPI Users hooks)
     - `C901`: Complex functions with justified linear flow (e.g., service startup)
   - Exception handling:
     - Use `logger.exception("message")` without `str(e)` - it automatically includes traceback
     - Add `from e` or `from None` to raise statements to maintain exception chain
   - Mutable class attributes:
     - Use `ClassVar` from typing for class-level mutable attributes
     - Example: `_cache: ClassVar[dict[str, Any]] = {}`
   - Prefer ternary operators for simple if-else assignments
     - `value = a if condition else b` instead of multi-line if-else
   - Store `os.getenv()` results once instead of calling multiple times

6. **Pre-commit hooks**
   - All code must pass pre-commit hooks before committing
   - Run `poetry run pre-commit run --all-files` before commit
   - Hooks include: ruff, ruff-format, bandit, detect-secrets, conventional commits

### Authentication

1. **FastAPI Users pattern**
   - User model inherits from `TimeStampedModel`
   - UserManager handles validation and hooks
   - Dependencies provide auth: `current_user`, `current_active_user`, `current_superuser`

2. **Password requirements (enforced in UserManager)**
   - Minimum 12 characters
   - At least one uppercase, lowercase, digit, special character
   - Uses bcrypt for hashing (via pwdlib)

3. **JWT configuration**
   - Secret key in `config.SECURITY.JWT_SECRET_KEY`
   - Token expiration in `config.SECURITY.JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
   - Bearer token transport at `/api/auth/bearer/login`

### Docker

1. **Multi-stage build targets**
   - `base` - System dependencies and EJSON CLI
   - `dependencies` - Python packages installed
   - `development` - Development environment with mounted source
   - `build` - Production build stage
   - `api` - Production API server
   - `worker` - Production Celery worker

2. **Docker development setup**
   - Uses `development` target with volume mounts for hot-reload
   - Source code mounted at `.:/app/src`
   - Poetry cache mounted at `./dockerdata/poetry-cache:/root/.cache/pypoetry`
   - Data persisted in gitignored `dockerdata/` folder:
     - `dockerdata/postgres-data` - PostgreSQL data
     - `dockerdata/redis-data` - Redis data
     - `dockerdata/poetry-cache` - Poetry cache

3. **EJSON in Docker**
   - Containers receive `EJSON_PUBLIC_KEY` and `EJSON_PRIVATE_KEY` as environment variables
   - Entrypoint scripts run `setup-ejson` to create keys in `ejson-keys/` directory
   - Then run `load-env` to decrypt and load secrets from `development.ejson`
   - `local.json` overrides are merged (but should not contain database/redis hosts in Docker)
   - `development.ejson` should contain Docker service names (postgres, redis)

4. **Environment configuration for Docker**
   - Database host: `postgres` (container name)
   - Database port: `5432` (internal container port)
   - Redis host: `redis` (container name)
   - Redis port: `6379` (internal container port)
   - Set in `secrets/development.json` before encrypting to EJSON

5. **Health checks**
   - Postgres: `pg_isready -U app -d app_db`
   - Redis: `redis-cli --raw incr ping`
   - API: `curl -f http://localhost:8000`
   - Worker: `celery -A app.worker.app inspect ping -d celery@worker`

### Repository Pattern

1. **Base repository methods**
   ```python
   # Available on all repositories
   await repo.get_by_id(id)
   await repo.find_by_attributes(**kwargs)
   await repo.find_one_by_attributes(**kwargs)
   await repo.create(obj)
   await repo.update(obj)
   await repo.delete(obj)
   ```

2. **Custom repository methods**
   ```python
   class UserRepository(Repository[User]):
       model_class = User

       async def get_by_email(self, email: str) -> Optional[User]:
           return await self.find_one_by_attributes(email=email)
   ```

### API Development

1. **Router structure**
   ```python
   router = APIRouter(prefix="/resource", tags=["resource"])

   @router.get("/")
   async def list_resources():
       pass
   ```

2. **Register in app.py**
   ```python
   from app.api.routes import new_router
   api_router.include_router(new_router.router)
   ```

3. **Dependency injection**
   ```python
   from fastapi import Depends
   from app.auth.dependencies import current_user

   @router.get("/protected")
   async def protected(user: User = Depends(current_user)):
       pass
   ```

## Project Structure

```
app/
├── api/              # HTTP layer
│   ├── middleware/   # Security, logging
│   ├── routes/       # Endpoints
│   └── app.py       # FastAPI factory
├── auth/             # Authentication module
│   ├── models.py     # User model
│   ├── repository.py # User data access
│   ├── dependencies.py # FastAPI Users setup
│   └── password/
│       ├── manager.py  # UserManager
│       └── router.py   # Auth endpoints
├── infra/            # Infrastructure
│   ├── database/     # DB connection, models, repository
│   ├── cache/        # Redis client
│   └── monitoring/   # Logging, tracing
├── worker/           # Celery workers
├── config.py         # Configuration
└── di.py            # Dependency injection

alembic/              # Database migrations
scripts/              # Utility scripts
secrets/              # Configuration files
docs/                 # Documentation
```

## Common Commands

```bash
# Development
poetry run poe serve api                        # Start API server
poetry run poe serve api --reload               # Start API with hot-reload
poetry run poe serve worker                     # Start Celery worker
poetry run poe serve worker --reload            # Start worker with hot-reload
poetry run poe serve worker --beat              # Start worker with beat scheduler

# Secrets Management
poetry run setup-ejson                          # Setup EJSON keys (requires EJSON_PUBLIC_KEY, EJSON_PRIVATE_KEY env vars)
poetry run encrypt-ejson development            # Encrypt secrets/development.json to development.ejson
poetry run decrypt-ejson development            # Decrypt secrets/development.ejson to development.json

# Database
poetry run poe migration-generate "description" # Create migration
poetry run poe migration-upgrade                # Apply migrations
poetry run poe migration-downgrade              # Rollback one migration

# Code Quality
poetry run ruff check app/                      # Lint
poetry run ruff format app/                     # Format
poetry run mypy app/                            # Type check
poetry run pytest                               # Run tests

# Docker
docker compose up                               # Start all services
docker compose up -d postgres redis             # Start specific services
docker compose logs api -f                      # Follow API logs
docker compose exec api bash                    # Shell into container
```

## Adding New Features

### 1. Create Model
```python
# app/domain/models.py (or create new module)
from app.infra.database.models import TimeStampedModel
from sqlmodel import Field

class Post(TimeStampedModel, table=True):
    __tablename__ = "posts"

    title: str = Field(max_length=255, index=True)
    content: str
    author_id: UUID = Field(foreign_key="users.id")
```

### 2. Create Repository
```python
# app/domain/repositories.py (or new file)
from app.infra.database.repository import Repository

class PostRepository(Repository[Post]):
    model_class = Post

    async def get_by_author(self, author_id: UUID):
        return await self.find_by_attributes(author_id=author_id)
```

### 3. Create Router
```python
# app/api/routes/posts.py
from fastapi import APIRouter, Depends
from app.auth.dependencies import current_user

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/")
async def list_posts(user: User = Depends(current_user)):
    # Implementation
    pass
```

### 4. Register Router
```python
# app/api/app.py
from app.api.routes import posts
api_router.include_router(posts.router)
```

### 5. Register Model in Alembic
```python
# alembic/env.py
with suppress(ImportError):
    from app.auth import models as auth_models
    from app.domain import models as domain_models  # Add this
```

### 6. Generate & Apply Migration
```bash
poetry run poe migration-generate "add posts table"
# Review generated migration
poetry run poe migration-upgrade
```

## Debugging Tips

1. **Database connection issues**
   - Check `secrets/local.json` has correct credentials
   - Verify PostgreSQL is running: `docker compose ps postgres`
   - Check logs: `docker compose logs postgres`

2. **Migration conflicts**
   - Check current state: `poetry run poe migration-current`
   - If stuck, downgrade: `poetry run poe migration-downgrade`
   - Delete problematic migration and regenerate

3. **Import errors**
   - Ensure virtual env is active: `poetry shell`
   - Check model is imported in `alembic/env.py`
   - Verify imports are in correct order

4. **Docker issues**
   - Rebuild with no cache: `docker compose build --no-cache`
   - Check environment variables: `docker compose config`
   - View container logs: `docker compose logs <service>`

## Testing

```python
# tests/conftest.py has fixtures for:
# - db_session: Database session
# - client: HTTP client
# - auth_client: Authenticated HTTP client

import pytest

@pytest.mark.asyncio
async def test_create_user(db_session):
    from app.auth.models import User
    user = User(email="test@example.com", full_name="Test")
    db_session.add(user)
    await db_session.commit()
    assert user.id is not None
```

## Documentation

Full documentation in `docs/`:
- [Getting Started](docs/01-getting-started.md)
- [Configuration](docs/02-configuration.md)
- [Database](docs/03-database.md)
- [Authentication](docs/04-authentication.md)
- [Docker & Deployment](docs/05-docker-deployment.md)
- [Development](docs/06-development.md)
- [Architecture](docs/07-architecture.md)

## Known Patterns

```python
# Repository Pattern
from app.infra.database.repository import Repository
from app.auth.models import User

class UserRepository(Repository[User]):
    model_class = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.find_one_by_attributes(email=email)

# Unit of Work Pattern (for transactions)
from app.infra.database.unit_of_work import UnitOfWork

@UnitOfWork.with_repositories(UserRepository, PostRepository)
async def create_user_with_post(user_data, post_data, uow=None):
    user_repo = uow.get_repository(UserRepository)
    post_repo = uow.get_repository(PostRepository)

    user = await user_repo.create(user_data)
    post = await post_repo.create(post_data)
    await uow.commit()
    return user

# Dependency Injection (FastAPI)
from fastapi import Depends
from app.auth.dependencies import current_active_user
from app.auth.models import User

@router.get("/protected")
async def endpoint(user: User = Depends(current_active_user)):
    ...

# Database session (when not using UnitOfWork)
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.database.db import get_session

@router.get("/")
async def simple_endpoint(session: AsyncSession = Depends(get_session)):
    ...

# Logging
from app.infra.monitoring.logging.logger import logger
logger.info("User created", extra={"user_id": str(user.id), "email": user.email})
# NEVER use structlog.get_logger(__name__) - use the global logger instance

# Dependency Injection for services needing config
# Services receive config through the DI container, not direct imports

# Example service with config injection
from app.config import DatabaseConfig

class MyService:
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config

# In DI container (di.py)
from dependency_injector import containers, providers

class MyContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    my_service = providers.Factory(
        MyService,
        db_config=config.DATABASE,
    )
```

## What NOT to Do

- ❌ Don't manually edit migrations
- ❌ Don't commit `secrets/local.json`
- ❌ Don't use "enhanced" or "extended" in names
- ❌ Don't bypass the repository pattern for database access
- ❌ Don't add default values to required config fields
- ❌ Don't modify Pydantic config to skip validation
- ❌ Don't create models without `table=True` and `__tablename__`
- ❌ Don't import config directly in services - use dependency injection from the container
