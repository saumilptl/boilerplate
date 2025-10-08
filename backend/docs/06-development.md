# Development Workflow

## Development Environment

### Local Setup

```bash
# 1. Install dependencies
poetry install

# 2. Configure environment
export ENVIRONMENT=development
cp secrets/local.json.example secrets/local.json

# 3. Start services
docker compose up -d postgres redis

# 4. Run migrations
poetry run poe migration-upgrade

# 5. Start dev server
poetry run poe dev
```

### IDE Setup

**VS Code Extensions:**
- Python
- Pylance
- Ruff
- SQLTools

**Settings (`.vscode/settings.json`):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## Code Quality

### Pre-commit Hooks

Automatically runs on every commit:

```bash
# Install hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

**Checks:**
- Ruff (linting + formatting)
- Bandit (security)
- Detect secrets
- Trailing whitespace
- End of file fixer
- YAML/JSON/TOML syntax
- Conventional commits

### Coding Standards

**Type Annotations:**
- All functions must have complete type hints
- Always include return type (including `-> None`)
```python
# Good
async def create_user(email: str, name: str) -> User:
    ...

async def send_notification(user_id: UUID) -> None:
    ...

# Bad
async def create_user(email, name):  # Missing types
    ...

async def send_notification(user_id: UUID):  # Missing return type
    ...
```

**Exception Handling:**
- Use `logger.exception()` without `str(e)` - it automatically includes traceback
- Always add `from e` or `from None` to maintain exception chain
```python
# Good
try:
    await risky_operation()
except ValueError as e:
    logger.exception("Operation failed")
    raise RuntimeError("Failed to process") from e

# Bad
try:
    await risky_operation()
except ValueError as e:
    logger.exception("Operation failed: %s", str(e))  # Don't use str(e)
    raise RuntimeError("Failed to process")  # Missing 'from'
```

**Class Attributes:**
- Use `ClassVar` for class-level mutable attributes
```python
from typing import ClassVar

class MyClass:
    # Good
    _cache: ClassVar[dict[str, Any]] = {}

    # Bad
    _cache: dict[str, Any] = {}  # Missing ClassVar
```

**Simplification:**
- Prefer ternary operators for simple conditionals
- Store repeated `os.getenv()` calls
```python
# Good
value = a if condition else b
env_var = os.getenv("KEY")
if env_var is not None:
    use(env_var)

# Bad
if condition:
    value = a
else:
    value = b

if os.getenv("KEY") is not None:
    use(os.getenv("KEY"))  # Called twice
```

**Using `noqa` Comments:**
- Minimize use - fix issues properly when possible
- Only use for legitimate cases:
  - `ARG002`: Interface methods with unused parameters required by parent class
  - `C901`: Functions with justified complexity (linear setup flows)
```python
# Good - interface method
async def on_after_register(
    self,
    user: User,
    request: Request | None = None  # noqa: ARG002
) -> None:
    logger.info("User registered", user_id=user.id)

# Good - justified complexity
def serve_worker(...) -> None:  # noqa: C901
    # Long linear setup flow with many sequential steps
    ...
```

### Linting

```bash
# Ruff - Fast Python linter
poetry run ruff check app/

# With auto-fix
poetry run ruff check --fix app/

# Format code
poetry run ruff format app/
```

### Type Checking

```bash
# Mypy - Static type checker
poetry run mypy app/

# Strict mode
poetry run mypy --strict app/
```

### Configuration

**pyproject.toml:**
```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "ARG", # flake8-unused-arguments
    "C90", # mccabe complexity
    "TRY", # tryceratops
    "SIM", # flake8-simplify
]

[tool.mypy]
python_version = "3.12"
strict = true
```

## Testing

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=app

# Specific test file
poetry run pytest tests/test_auth.py

# Specific test
poetry run pytest tests/test_auth.py::test_user_registration

# Watch mode
poetry run ptw
```

### Writing Tests

**Test structure:**
```
tests/
├── conftest.py           # Fixtures
├── unit/                 # Unit tests
│   ├── test_models.py
│   └── test_repositories.py
├── integration/          # Integration tests
│   ├── test_auth_flow.py
│   └── test_api.py
└── e2e/                  # End-to-end tests
    └── test_user_journey.py
```

**Example test:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
```

### Fixtures

**conftest.py:**
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.fixture
async def db_session():
    # Create test database
    engine = create_async_engine("postgresql+asyncpg://localhost/test_db")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## Poetry Commands

### Dependency Management

```bash
# Add package
poetry add fastapi

# Add dev dependency
poetry add --group dev pytest

# Update dependencies
poetry update

# Show outdated
poetry show --outdated

# Lock file only
poetry lock --no-update
```

### Custom Commands (Poe Tasks)

Defined in `pyproject.toml`:

```toml
[tool.poe.tasks]
dev = "uvicorn app.api.app:app --host 0.0.0.0 --port 8000 --reload"
worker = "celery -A app.worker.celery_app worker --loglevel=info"
migration-generate = "python -m scripts.database.migrations generate"
migration-upgrade = "python -m scripts.database.migrations upgrade"
test = "pytest"
lint = "ruff check app/"
format = "ruff format app/"
typecheck = "mypy app/"
```

**Usage:**
```bash
poetry run poe dev
poetry run poe migration-generate "add users table"
```

## Git Workflow

### Branch Strategy

```
main           ← Production
  ↑
development    ← Integration
  ↑
feature/*      ← Feature branches
bugfix/*       ← Bug fixes
hotfix/*       ← Production hotfixes
```

### Commit Messages

Follow conventional commits:

```
feat: add user registration endpoint
fix: resolve database connection pool exhaustion
docs: update authentication documentation
refactor: simplify config loading
test: add user repository tests
chore: update dependencies
```

### Creating Features

```bash
# Create feature branch
git checkout -b feature/user-profiles

# Make changes
git add .
git commit -m "feat: add user profile model"

# Push and create PR
git push -u origin feature/user-profiles
```

## Database Development

### Creating Migrations

```bash
# Auto-generate from models
poetry run poe migration-generate "add user profiles"

# Review generated migration
# Edit if needed: alembic/versions/xxx_add_user_profiles.py

# Test migration
poetry run poe migration-upgrade

# Test rollback
poetry run poe migration-downgrade
```

### Database Debugging

```bash
# PostgreSQL shell
psql postgresql://app:password@localhost:5433/app_db

# Useful queries
\dt                  # List tables
\d users             # Describe table
\l                   # List databases
\c app_db            # Connect to database

# Check migration status
SELECT * FROM alembic_version;
```

## API Development

### Adding Endpoints

1. **Create router:**
```python
# app/api/routes/posts.py
from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/")
async def list_posts():
    return {"posts": []}
```

2. **Register router:**
```python
# app/api/app.py
from app.api.routes import posts

api_router.include_router(posts.router)
```

3. **Test endpoint:**
```bash
curl http://localhost:8000/api/posts
```

### Request/Response Models

```python
from pydantic import BaseModel

class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: UUID
    title: str
    content: str
    created_at: datetime

@router.post("/", response_model=PostResponse)
async def create_post(post: PostCreate):
    # ...
    return created_post
```

## Worker Development

### Creating Tasks

```python
# app/worker/tasks/notifications.py
from app.worker.celery_app import celery_app

@celery_app.task(name="send_email")
def send_email(to: str, subject: str, body: str):
    # Send email logic
    return {"sent": True}
```

### Running Tasks

```python
# Async
from app.worker.tasks.notifications import send_email

send_email.delay("user@example.com", "Welcome", "Hello!")

# Get result
result = send_email.apply_async(
    args=["user@example.com", "Welcome", "Hello!"]
)
print(result.get(timeout=10))
```

### Monitoring Tasks

```bash
# List active tasks
poetry run celery -A app.worker.celery_app inspect active

# Task stats
poetry run celery -A app.worker.celery_app inspect stats

# Flower UI
poetry run celery -A app.worker.celery_app flower
# Open http://localhost:5555
```

## Debugging

### Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in
breakpoint()
```

### VS Code Debugging

**launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.api.app:app",
        "--reload"
      ],
      "jinja": true
    }
  ]
}
```

### Logging

```python
from app.infra.monitoring.logging.logger import logger

logger.info("User created", user_id=user.id, email=user.email)
logger.error("Failed to send email", error=str(e))
```

**Important:** Always use the global logger instance from `app.infra.monitoring.logging.logger`. Do not create new logger instances with `structlog.get_logger(__name__)`.

## Performance Profiling

### Request Profiling

```python
import time
from fastapi import Request

@app.middleware("http")
async def profile_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("Request completed",
        path=request.url.path,
        duration=duration
    )
    return response
```

### Database Query Profiling

```python
# Enable SQL echo
# In secrets/local.json
{
  "DATABASE": {
    "ECHO": true
  }
}
```

## Hot Reload

### API Server

```bash
# Automatic reload on file changes
poetry run poe dev

# Or manually
poetry run uvicorn app.api.app:app --reload
```

### Worker

```bash
# With watchdog
poetry run watchmedo auto-restart \
  --directory=app/worker \
  --pattern=*.py \
  --recursive \
  -- celery -A app.worker.celery_app worker
```

## Common Tasks

### Reset Database

```bash
# Drop all tables
poetry run poe migration-downgrade base

# Recreate
poetry run poe migration-upgrade
```

### Seed Data

```python
# scripts/seed_data.py
async def seed():
    async with get_session() as session:
        users = [
            User(email=f"user{i}@example.com", ...)
            for i in range(10)
        ]
        session.add_all(users)
        await session.commit()

# Run
poetry run python scripts/seed_data.py
```

### Generate OpenAPI Schema

```bash
# Export schema
curl http://localhost:8000/openapi.json > openapi.json

# Generate client
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o client/
```

## Troubleshooting

### Import Errors

```bash
# Verify imports
poetry run python -c "from app.config import config; print(config())"

# Check sys.path
poetry run python -c "import sys; print('\\n'.join(sys.path))"
```

### Dependency Conflicts

```bash
# Show dependency tree
poetry show --tree

# Update lock file
poetry lock --no-update

# Reinstall
poetry install --sync
```

### Port Conflicts

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in local.json
{
  "PORT": 8001
}
```
