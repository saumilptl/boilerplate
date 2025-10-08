# Authentication & Authorization

## Overview

Authentication is handled by **FastAPI Users**, providing:
- User registration and management
- JWT bearer token authentication
- Password reset functionality
- Email verification (structure in place)
- Account locking on failed attempts

## User Model

```python
# app/auth/models.py
class User(TimeStampedModel, table=True):
    id: uuid.UUID              # Primary key
    email: str                 # Unique, indexed
    hashed_password: str       # Bcrypt hashed
    full_name: str

    # Status flags
    is_active: bool            # Account active
    is_verified: bool          # Email verified
    is_superuser: bool         # Admin privileges

    # Security tracking
    last_login: datetime
    password_changed_at: datetime
    failed_login_attempts: int
    locked_until: datetime
```

## Password Requirements

Enforced by `UserManager.validate_password()`:

- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?/`~)

## Authentication Endpoints

### User Registration

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}

# Response: 201 Created
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "created_at": "2025-10-07T12:00:00Z"
}
```

### Login (JWT Bearer)

```bash
POST /api/auth/bearer/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePassword123!

# Response: 200 OK
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### Get Current User

```bash
GET /api/auth/users/me
Authorization: Bearer eyJhbGci...

# Response: 200 OK
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "is_superuser": false,
  "created_at": "2025-10-07T12:00:00Z"
}
```

### Update User

```bash
PATCH /api/auth/users/me
Authorization: Bearer eyJhbGci...
Content-Type: application/json

{
  "full_name": "Jane Doe"
}
```

### Password Reset Request

```bash
POST /api/auth/forgot-password/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}

# Response: 202 Accepted
# (Reset token would be sent via email)
```

### Password Reset Confirm

```bash
POST /api/auth/forgot-password/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "password": "NewSecurePassword123!"
}
```

### Logout

```bash
POST /api/auth/bearer/logout
Authorization: Bearer eyJhbGci...

# Response: 200 OK
```

## Using Authentication in Routes

### Require Authenticated User

```python
from fastapi import APIRouter, Depends
from app.auth.dependencies import current_active_user
from app.auth.models import User

router = APIRouter()

@router.get("/protected")
async def protected_route(
    user: User = Depends(current_active_user)
):
    return {"message": f"Hello {user.email}"}
```

### Require Verified User

```python
from app.auth.dependencies import current_user

@router.get("/verified-only")
async def verified_route(
    user: User = Depends(current_user)  # active=True, verified=True
):
    return {"message": "You are verified"}
```

### Require Superuser

```python
from app.auth.dependencies import current_superuser

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: UUID,
    admin: User = Depends(current_superuser)
):
    # Only superusers can access this
    return {"deleted": user_id}
```

### Optional Authentication

```python
from typing import Optional
from app.auth.dependencies import fastapi_users

current_user_optional = fastapi_users.current_user(optional=True)

@router.get("/public")
async def public_route(
    user: Optional[User] = Depends(current_user_optional)
):
    if user:
        return {"message": f"Hello {user.email}"}
    return {"message": "Hello anonymous"}
```

## Security Features

### Account Locking

Implemented in `UserManager.on_before_login()`:

- Tracks failed login attempts per email
- Locks account after threshold exceeded
- Automatic unlock after timeout
- Resets counter after 30 minutes

**Configuration:**
```python
# In UserManager
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
```

### JWT Configuration

Set in `secrets/{environment}.ejson`:

```json
{
  "SECURITY": {
    "JWT_SECRET_KEY": "your-secret-key-change-in-production",
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS": 7
  }
}
```

**Important:** Change `JWT_SECRET_KEY` in production!

```bash
# Generate a secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Password Hashing

Uses **bcrypt** via pwdlib:
- Automatic salt generation
- Configurable rounds (default: 12)
- Secure against rainbow table attacks

## User Repository

Custom repository for user operations:

```python
from app.auth.repository import UserRepository
from app.infra.database.db import get_session

async def get_user_by_email(email: str):
    async with get_session() as session:
        repo = UserRepository(session)
        return await repo.get_by_email(email)

# Other methods:
# - find_active_users()
# - find_verified_users()
# - find_superusers()
# - find_locked_users()
# - update_login_status(user_id, success)
```

## Customizing UserManager

Add custom logic in `app/auth/password/manager.py`:

```python
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):

    async def on_after_register(self, user: User, request: Request):
        # Send welcome email
        await send_welcome_email(user.email)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request
    ):
        # Send password reset email
        await send_reset_email(user.email, token)

    async def on_after_login(
        self, user: User, request: Request, response: Response
    ):
        # Log successful login
        logger.info(f"User {user.id} logged in")
```

## Testing Authentication

### Pytest Fixtures

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def test_user(db_session):
    from app.auth.models import User
    user = User(
        email="test@example.com",
        hashed_password="hashed...",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.fixture
async def auth_client(test_user):
    # Login and get token
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/bearer/login",
            data={
                "username": test_user.email,
                "password": "password"
            }
        )
        token = response.json()["access_token"]

        # Set auth header
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
```

### Testing Protected Routes

```python
@pytest.mark.asyncio
async def test_protected_route(auth_client):
    response = await auth_client.get("/api/protected")
    assert response.status_code == 200
```

## CORS Configuration

For frontend integration:

```json
{
  "SECURITY": {
    "CORS_ORIGINS": [
      "http://localhost:3000",
      "https://app.example.com"
    ],
    "CORS_ALLOW_CREDENTIALS": true
  }
}
```

## Rate Limiting

Configured in security settings:

```json
{
  "SECURITY": {
    "RATE_LIMIT_ENABLED": true,
    "RATE_LIMIT_PER_MINUTE": 60
  }
}
```

Applied via middleware in `app/api/middleware/security.py`.

## Common Patterns

### Check User Permissions

```python
from fastapi import HTTPException

async def require_permission(
    user: User,
    permission: str
):
    if not user.has_permission(permission):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
```

### Multi-Tenant Support

```python
# Add organization_id to User model
class User(TimeStampedModel, table=True):
    organization_id: Optional[UUID] = Field(foreign_key="organizations.id")

# Filter by organization
async def get_organization_users(
    user: User = Depends(current_user)
):
    return await UserRepository(session).find_by_attributes(
        organization_id=user.organization_id
    )
```

## Troubleshooting

### 401 Unauthorized

- Check token format: `Bearer <token>`
- Verify token hasn't expired
- Check JWT_SECRET_KEY matches

### 403 Forbidden

- User lacks required permissions
- Account may be inactive or unverified

### Password Validation Errors

- Review `UserManager.validate_password()`
- Check minimum requirements met

### Account Locked

- Too many failed login attempts
- Wait for lockout period to expire
- Admin can manually unlock via database
