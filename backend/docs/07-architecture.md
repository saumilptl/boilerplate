# Architecture

## System Overview

The boilerplate follows Clean Architecture principles with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  Routes, Middleware, Request/Response   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       Application Layer (Auth)          │
│    Business Logic, Use Cases            │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│   Infrastructure Layer (Database, etc)  │
│  Repositories, External Services        │
└─────────────────────────────────────────┘
```

## Project Structure

```
app/
├── api/                    # HTTP API Layer
│   ├── app.py             # FastAPI application factory
│   ├── middleware/        # Security, CORS, rate limiting
│   │   ├── security.py
│   │   └── logging.py
│   └── routes/            # API endpoints
│       └── health.py
│
├── auth/                   # Authentication Module
│   ├── models.py          # User model
│   ├── repository.py      # User data access
│   ├── dependencies.py    # FastAPI Users setup
│   └── password/
│       ├── manager.py     # Password validation, user hooks
│       └── router.py      # Auth endpoints
│
├── infra/                  # Infrastructure Layer
│   ├── database/
│   │   ├── db.py          # Database connection
│   │   ├── models.py      # Base models
│   │   ├── repository.py  # Base repository pattern
│   │   └── unit_of_work.py
│   ├── cache/
│   │   └── redis.py       # Redis client
│   └── monitoring/
│       ├── logging/       # Structured logging
│       └── tracer.py      # OpenTelemetry/Datadog
│
├── worker/                 # Celery Workers
│   ├── celery_app.py      # Celery configuration
│   └── tasks/             # Background tasks
│
├── config.py              # Configuration management
└── di.py                  # Dependency injection container

alembic/                   # Database Migrations
├── versions/              # Migration files
└── env.py                 # Alembic environment

scripts/                   # Utility Scripts
├── database/
│   └── migrations.py      # Migration commands
├── docker/
│   ├── api.entrypoint.sh  # API container entrypoint
│   └── worker.entrypoint.sh
└── secrets/
    └── secret_loader.py   # EJSON decryption

secrets/                   # Configuration Files
├── development.ejson      # Development config
├── staging.ejson          # Staging config
├── production.ejson       # Production config
└── local.json            # Local overrides (gitignored)
```

## Layered Architecture

### 1. API Layer

**Responsibility:** HTTP interface, request/response handling

```python
# app/api/routes/users.py
from fastapi import APIRouter, Depends
from app.auth.dependencies import current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def get_current_user(user: User = Depends(current_user)):
    return user
```

**Key Components:**
- Route handlers
- Request/response models (Pydantic)
- Middleware (auth, CORS, rate limiting)
- Exception handlers

### 2. Application Layer

**Responsibility:** Business logic, use cases

```python
# app/auth/password/manager.py
class UserManager(BaseUserManager):
    async def on_after_register(self, user: User, request: Request):
        # Business logic: send welcome email
        await send_welcome_email(user)

    async def validate_password(self, password: str, user: User):
        # Business rule: password requirements
        if len(password) < 12:
            raise ValidationError("Password too short")
```

**Key Components:**
- Domain models
- Business rules validation
- Use case orchestration
- Domain events

### 3. Infrastructure Layer

**Responsibility:** External integrations, data persistence

```python
# app/infra/database/repository.py
class Repository(Generic[T]):
    async def get_by_id(self, id: UUID) -> Optional[T]:
        query = select(self.model_class).where(
            self.model_class.id == id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
```

**Key Components:**
- Database repositories
- External API clients
- Caching layer
- Message queue integration

## Design Patterns

### Repository Pattern

Abstracts data access:

```python
class UserRepository(Repository[User]):
    model_class = User

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.find_one_by_attributes(email=email)

# Usage
async with get_session() as session:
    repo = UserRepository(session)
    user = await repo.get_by_email("test@example.com")
```

**Benefits:**
- Decouples business logic from data access
- Makes testing easier (mock repository)
- Centralizes query logic

### Unit of Work Pattern

Manages transactions:

```python
async with container.database.unit_of_work() as uow:
    # All operations in single transaction
    user = User(email="test@example.com")
    uow.session.add(user)

    profile = Profile(user_id=user.id)
    uow.session.add(profile)

    await uow.commit()  # Atomic commit
```

**Benefits:**
- Ensures data consistency
- Simplifies transaction management
- Supports rollback on errors

### Dependency Injection

Uses `dependency-injector`:

```python
# app/di.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    database = providers.Singleton(
        Database,
        config=config.DATABASE
    )

    redis = providers.Singleton(
        RedisClient,
        config=config.REDIS
    )

# Usage
container = get_container()
db = container.database()
```

**Benefits:**
- Loose coupling
- Easier testing (swap implementations)
- Centralized configuration

### Factory Pattern

Creates complex objects:

```python
# app/api/app.py
def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(...)

    # Add middleware
    add_security_middleware(app, config.SECURITY)

    # Register routers
    app.include_router(api_router)

    return app
```

**Benefits:**
- Flexible application configuration
- Supports multiple instances (testing)
- Centralizes setup logic

## Data Flow

### Request Flow

```
1. HTTP Request
   ↓
2. Middleware (CORS, Auth, Logging)
   ↓
3. Route Handler
   ↓
4. Dependency Injection (get current user, session)
   ↓
5. Repository (database query)
   ↓
6. Response Model (Pydantic)
   ↓
7. HTTP Response
```

### Authentication Flow

```
1. Login Request (username + password)
   ↓
2. UserManager.authenticate()
   ↓
3. Password verification (bcrypt)
   ↓
4. JWT token generation
   ↓
5. Return access_token
   ↓
6. Client stores token
   ↓
7. Subsequent requests include: Authorization: Bearer {token}
   ↓
8. JWT verification
   ↓
9. Load user from database
   ↓
10. Inject user into route handler
```

### Background Task Flow

```
1. API endpoint enqueues task
   ↓
2. Celery worker picks up task
   ↓
3. Task executes (e.g., send email)
   ↓
4. Result stored in Redis
   ↓
5. API can query task status
```

## Database Design

### Schema Principles

1. **UUID Primary Keys** - Better for distributed systems
2. **Timestamps** - Track creation and updates
3. **Soft Deletes** - Mark as deleted, don't remove
4. **Audit Trails** - Track who created/updated
5. **Indexes** - On foreign keys and frequently queried columns

### Base Models

```python
class BaseModel(SQLModel):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)

class TimeStampedModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )

class AuditableModel(BaseModel):
    created_by_id: Optional[UUID] = Field(foreign_key="users.id")
    updated_by_id: Optional[UUID] = Field(foreign_key="users.id")

class SoftDeleteModel(BaseModel):
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[UUID] = Field(foreign_key="users.id")
```

## Security Architecture

### Defense in Depth

```
┌──────────────────────────────────────┐
│  1. HTTPS/TLS (Transport Security)   │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  2. CORS (Cross-Origin Protection)   │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  3. Rate Limiting (DDoS Protection)  │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  4. JWT Auth (Authentication)        │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  5. RBAC (Authorization)             │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  6. Input Validation (Pydantic)      │
└──────────────────────────────────────┘
```

### Security Best Practices

1. **Secrets Management** - EJSON encryption
2. **Password Hashing** - bcrypt with salt
3. **JWT Tokens** - Short expiration, secure secret
4. **SQL Injection Prevention** - Parameterized queries (SQLAlchemy)
5. **XSS Prevention** - Automatic escaping in responses
6. **CSRF Protection** - SameSite cookies
7. **Rate Limiting** - Per-IP request limits

## Configuration Management

### Hierarchical Configuration

```
Priority (highest to lowest):
1. ENV_ environment variables (runtime)
2. local.json (development only)
3. {environment}.ejson (base configuration)
```

### Configuration Flow

```python
# 1. Load EJSON
secrets_loader = SecretsLoader(environment="development")
ejson_config = secrets_loader.load_ejson_secrets()

# 2. Merge ENV_ variables
for key, value in os.environ.items():
    if key.startswith("ENV_"):
        config_key = key[4:]  # Remove ENV_ prefix
        ejson_config[config_key] = parse_value(value)

# 3. Merge local.json (dev only)
if environment == "development" and local_json.exists():
    local_config = json.load(open(local_json))
    deep_merge(ejson_config, local_config)

# 4. Create config object
config = Config(**ejson_config)
```

## Monitoring & Observability

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "User registered",
    user_id=user.id,
    email=user.email,
    service="backend-api"
)
```

**Log Levels:**
- DEBUG: Development debugging
- INFO: Normal operations
- WARNING: Unexpected but handled
- ERROR: Error requiring attention
- CRITICAL: System failure

### Tracing

OpenTelemetry integration for distributed tracing:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("database_query"):
    users = await session.execute(select(User))
```

### Metrics

Key metrics to monitor:
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Database connection pool usage
- Worker queue depth

## Scalability

### Horizontal Scaling

```
┌─────────┐   ┌─────────┐   ┌─────────┐
│  API 1  │   │  API 2  │   │  API 3  │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │             │
     └─────────┬───┴─────────────┘
               │
        ┌──────▼──────┐
        │  Load Bal.  │
        └──────┬──────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼────┐      ┌──────▼────┐
│Database │      │   Redis   │
│ (Master)│      │           │
└─────────┘      └───────────┘
```

### Async Processing

```python
# Fast response, slow processing
@router.post("/process")
async def process_data(data: Data):
    # Queue task, return immediately
    task = process_task.delay(data.id)
    return {"task_id": task.id}

# Check status later
@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id)
    return {"status": result.status}
```

## Testing Strategy

### Test Pyramid

```
        ┌────────────┐
        │    E2E     │  Few, slow, high value
        └────────────┘
      ┌──────────────┐
      │ Integration  │  Some, medium speed
      └──────────────┘
    ┌──────────────────┐
    │      Unit        │  Many, fast, focused
    └──────────────────┘
```

**Unit Tests:** Test individual functions/classes
**Integration Tests:** Test multiple components together
**E2E Tests:** Test full user workflows

## Performance Optimization

### Database Optimization

1. **Connection Pooling** - Reuse connections
2. **Indexes** - Speed up queries
3. **Query Optimization** - Use `selectinload` for joins
4. **Pagination** - Limit result sets

### Caching Strategy

```python
# Redis caching
@cache(ttl=3600)
async def get_user(user_id: UUID):
    return await db.query(User).get(user_id)
```

### Async Processing

```python
# Use async/await for I/O operations
async def get_users():
    async with get_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()
```

## Future Enhancements

Potential improvements:
- [ ] GraphQL API
- [ ] WebSocket support
- [ ] Event sourcing
- [ ] CQRS pattern
- [ ] Microservices architecture
- [ ] gRPC for inter-service communication
- [ ] Kubernetes deployment
- [ ] Service mesh (Istio)
