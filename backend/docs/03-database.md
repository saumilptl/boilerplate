# Database & Migrations

## Overview

- **ORM:** SQLModel (SQLAlchemy 2.0 + Pydantic)
- **Migrations:** Alembic
- **Driver:** asyncpg (async PostgreSQL)
- **Connection Pooling:** Built-in with configurable settings

## Database Models

### Base Models

All models inherit from base classes in `app/infra/database/models.py`:

```python
from app.infra.database.models import BaseModel, TimeStampedModel

class User(TimeStampedModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    # ... more fields
```

**Available Base Models:**
- `BaseModel` - Provides UUID primary key
- `TimeStampedModel` - Adds created_at, updated_at
- `AuditableModel` - Adds created_by_id, updated_by_id
- `SoftDeleteModel` - Adds deleted_at, deleted_by_id

### Model Guidelines

1. **Always set `table=True`** for database tables
2. **Define `__tablename__`** explicitly
3. **Use `Field()` for column configuration**
4. **Add indexes** on frequently queried columns
5. **Define relationships** with `Relationship()`

### Example Model

```python
from uuid import UUID
from sqlmodel import Field, Relationship
from app.infra.database.models import TimeStampedModel

class Post(TimeStampedModel, table=True):
    __tablename__ = "posts"

    # Primary key (inherited from BaseModel via TimeStampedModel)
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Fields with constraints
    title: str = Field(index=True, max_length=255)
    content: str = Field(sa_column=Column(Text))
    published: bool = Field(default=False)

    # Foreign key
    author_id: UUID = Field(foreign_key="users.id")

    # Relationship
    author: "User" = Relationship(back_populates="posts")
```

## Repository Pattern

Use repositories for database operations:

```python
from app.infra.database.repository import Repository

class UserRepository(Repository[User]):
    model_class = User

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.find_one_by_attributes(email=email)

    async def find_active(self) -> Sequence[User]:
        return await self.find_by_attributes(is_active=True)
```

**Base Repository Methods:**
- `get_by_id(id)` - Get by primary key
- `find_by_attributes(**kwargs)` - Find many
- `find_one_by_attributes(**kwargs)` - Find one
- `create(obj)` - Create new record
- `update(obj)` - Update existing
- `delete(obj)` - Delete record

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
poetry run poe migration-generate "description of changes"

# Example
poetry run poe migration-generate "add email verification to users"
```

### Applying Migrations

```bash
# Upgrade to latest
poetry run poe migration-upgrade

# Upgrade to specific version
poetry run poe migration-upgrade <revision>

# Downgrade one version
poetry run poe migration-downgrade

# Downgrade to specific version
poetry run poe migration-downgrade <revision>
```

### Migration Status

```bash
# Show current version
poetry run poe migration-current

# Show migration history
poetry run poe migration-history

# Show pending migrations
poetry run poe migration-pending
```

### Manual Migrations

When auto-generate doesn't capture everything:

```python
"""add user verification

Revision ID: abc123
Revises: def456
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.add_column('users',
        sa.Column('verified_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.create_index('ix_users_verified_at', 'users', ['verified_at'])

def downgrade() -> None:
    op.drop_index('ix_users_verified_at', 'users')
    op.drop_column('users', 'verified_at')
```

### Migration Best Practices

1. **Always review** auto-generated migrations
2. **Test migrations** on copy of production data
3. **Include rollback logic** in downgrade()
4. **Keep migrations atomic** - one logical change per migration
5. **Never modify** existing migrations after they're merged
6. **Add data migrations** carefully to avoid locking tables

## Database Sessions

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.database.db import get_session

@router.get("/users")
async def list_users(
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User))
    return result.scalars().all()
```

### Unit of Work Pattern

For complex transactions:

```python
from app.infra.database.unit_of_work import UnitOfWork
from app.di import get_container

container = get_container()

async with container.database.unit_of_work() as uow:
    # Create user
    user = User(email="test@example.com")
    uow.session.add(user)

    # Create related records
    profile = Profile(user_id=user.id)
    uow.session.add(profile)

    # Commit transaction
    await uow.commit()
```

## Database Connection

### Configuration

Set in `secrets/{environment}.ejson`:

```json
{
  "DATABASE": {
    "HOST": "localhost",
    "PORT": 5432,
    "USER": "app",
    "PASSWORD": "secret",
    "NAME": "app_db",
    "DRIVER": "postgresql+asyncpg",
    "SSL_MODE": "prefer",
    "POOL_SIZE": 25,
    "MAX_OVERFLOW": 50,
    "POOL_RECYCLE": 3600,
    "POOL_PRE_PING": true,
    "ECHO": false
  }
}
```

### Connection Pool Settings

- `POOL_SIZE: 25` - Number of persistent connections
- `MAX_OVERFLOW: 50` - Additional connections when pool exhausted
- `POOL_RECYCLE: 3600` - Recycle connections after 1 hour
- `POOL_PRE_PING: true` - Test connections before use

### Connection String

Automatically generated from config:

```python
from app.config import config

cfg = config()

# Async (asyncpg)
async_url = cfg.DATABASE.async_url
# postgresql+asyncpg://app:secret@localhost:5432/app_db

# Sync (psycopg2) - for Alembic
sync_url = cfg.DATABASE.sync_url
# postgresql://app:secret@localhost:5432/app_db
```

## Raw SQL Queries

When needed:

```python
from sqlalchemy import text

async with get_session() as session:
    result = await session.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": "test@example.com"}
    )
    user = result.first()
```

## Testing Database

### Test Database Setup

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.fixture
async def db_session():
    # Create test database
    engine = create_async_engine("postgresql+asyncpg://localhost/test_db")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    async with AsyncSession(engine) as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
```

### Using Test Database

```python
@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(email="test@example.com", full_name="Test User")
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
```

## Common Patterns

### Pagination

```python
from sqlalchemy import select

async def get_users_paginated(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20
):
    offset = (page - 1) * per_page
    query = select(User).offset(offset).limit(per_page)
    result = await session.execute(query)
    return result.scalars().all()
```

### Filtering

```python
from sqlalchemy import select, and_, or_

query = select(User).where(
    and_(
        User.is_active == True,
        or_(
            User.email.like("%@example.com"),
            User.full_name.like("Test%")
        )
    )
)
```

### Joins

```python
from sqlalchemy.orm import selectinload

query = select(User).options(
    selectinload(User.posts)
)
result = await session.execute(query)
users = result.scalars().all()
```

### Aggregations

```python
from sqlalchemy import func

query = select(
    func.count(User.id),
    User.is_active
).group_by(User.is_active)

result = await session.execute(query)
```

## Troubleshooting

### Migration Conflicts

```bash
# Show current head
poetry run poe migration-current

# Check for multiple heads
alembic heads

# Merge heads
alembic merge -m "merge heads" head1 head2
```

### Connection Pool Exhausted

Increase pool size in config:
```json
{
  "DATABASE": {
    "POOL_SIZE": 50,
    "MAX_OVERFLOW": 100
  }
}
```

### Slow Queries

Enable query logging:
```json
{
  "DATABASE": {
    "ECHO": true
  }
}
```

### Database Locked

Check for long-running transactions:
```sql
SELECT pid, age(clock_timestamp(), query_start), query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;
```
