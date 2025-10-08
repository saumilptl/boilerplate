# Claude Development Guidelines - Fullstack Boilerplate

This document provides context for AI assistants working on this fullstack monorepo.

## Project Overview

Production-ready fullstack monorepo with:

**Backend:**
- FastAPI with async Python
- PostgreSQL + SQLModel ORM
- Alembic migrations
- Celery workers with Redis
- FastAPI Users authentication (JWT bearer + cookie)
- EJSON encrypted secrets
- Docker multi-stage builds

**Frontend:**
- SvelteKit 2.0 with Svelte 5
- Tailwind CSS v4
- shadcn-svelte UI components
- Cookie-based authentication
- Type-safe API client with Zod

**Infrastructure:**
- Caddy reverse proxy
- Docker Compose orchestration
- Separate pre-commit hooks per workspace
- Monorepo-friendly .gitignore strategy

## Critical Rules

### Monorepo Structure

1. **Backend in `/backend/`**
   - Self-contained Python project with own dependencies
   - Has own .gitignore for Python-specific ignores
   - See [backend/CLAUDE.md](backend/CLAUDE.md) for backend-specific rules

2. **Frontend in `/frontend/`**
   - Self-contained Node.js project with own dependencies
   - Has own .gitignore for Node-specific ignores
   - See [frontend/CLAUDE.md](frontend/CLAUDE.md) for frontend-specific rules

3. **Root-level concerns**
   - Docker Compose orchestration
   - Caddy reverse proxy configuration
   - Monorepo-wide pre-commit hooks
   - Minimal .gitignore for shared concerns only

### Naming Conventions

**CRITICAL:** Never use "enhanced", "extended", "improved", or similar generic prefixes in names.

```python
# ✅ Good
class UserAuthenticationManager: ...
class DatabaseConnectionPool: ...

# ❌ Bad
class EnhancedUserManager: ...
class ImprovedDatabase: ...
```

This rule applies to:
- Functions and classes
- Files and directories
- Variables and constants
- Database tables and columns
- API endpoints
- Component names

### Code Quality

1. **Type Safety**
   - Backend: Type hints required for all functions
   - Frontend: TypeScript strict mode with Zod validation
   - Both: Explicit return types

2. **Linting Standards**
   - Backend: Ruff (minimize `noqa` usage)
   - Frontend: ESLint + Prettier (minimize disable comments)
   - Fix issues properly, not with suppressions

3. **Pre-commit Hooks**
   - Scoped hooks for backend (`^backend/`) and frontend (`^frontend/`)
   - All code must pass before committing
   - Run manually: `pre-commit run --all-files`

## Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── alembic/            # Database migrations
│   ├── scripts/            # Utility scripts
│   ├── secrets/            # EJSON configuration
│   ├── docs/               # Backend documentation
│   ├── CLAUDE.md           # Backend-specific guidelines
│   ├── pyproject.toml      # Python dependencies
│   └── .gitignore          # Python-specific ignores
│
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── lib/           # Reusable code
│   │   └── routes/        # File-based routing
│   ├── static/            # Static assets
│   ├── docs/              # Frontend documentation
│   ├── CLAUDE.md          # Frontend-specific guidelines
│   ├── package.json       # Node dependencies
│   └── .gitignore         # Node-specific ignores
│
├── docs/                   # Monorepo documentation
├── Caddyfile              # Reverse proxy config
├── docker-compose.yaml    # Container orchestration
├── .pre-commit-config.yaml # Monorepo hooks
├── .gitignore             # Root-level ignores only
└── CLAUDE.md              # This file
```

## Architecture

### Request Flow

```
Client Request
    ↓
Caddy Reverse Proxy (:8080)
    ↓
    ├─ /api/* → Backend API (:8000)
    │              ↓
    │          FastAPI Routes
    │              ↓
    │          Business Logic
    │              ↓
    │          PostgreSQL / Redis
    │
    └─ /app/* → Frontend (:5173)
                   ↓
               SvelteKit SSR
                   ↓
               Svelte Components
```

### Authentication Flow

```
1. User submits login form
    ↓
2. Frontend → POST /api/auth/cookie/login (form-urlencoded)
    ↓
3. Backend validates credentials
    ↓
4. Backend sets HttpOnly cookie (auth-token)
    ↓
5. Frontend fetches user: GET /api/auth/users/me (cookie auto-sent)
    ↓
6. Frontend stores user in auth state
    ↓
7. Protected routes check auth state
```

### Data Flow

```
Frontend Component
    ↓
State Store (Svelte 5 runes)
    ↓
Service Function (lib/api/*.ts)
    ↓
API Client (with Zod validation)
    ↓
HTTP Request (credentials: include)
    ↓
Backend Route
    ↓
Repository Pattern
    ↓
Database (PostgreSQL)
```

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| `postgres` | 5433 (external) | PostgreSQL database |
| `redis` | 6379 (internal) | Cache and Celery broker |
| `api` | 8000 (internal) | FastAPI backend |
| `worker` | - | Celery background tasks |
| `frontend` | 5173 (internal) | SvelteKit dev server |
| `caddy` | 8080 (external) | Reverse proxy |

**Access:**
- Frontend: `http://localhost:8080/app`
- Backend API: `http://localhost:8080/api`
- API Docs: `http://localhost:8080/api/docs`

## Development Workflow

### Initial Setup

```bash
# 1. Setup backend
cd backend
poetry install
cp secrets/local.json.example secrets/local.json
# Edit secrets/local.json

# 2. Setup frontend
cd ../frontend
npm install

# 3. Start all services
cd ..
docker compose up
```

### Daily Development

**Using Docker (recommended):**
```bash
# Start all services
docker compose up

# View logs
docker compose logs -f api
docker compose logs -f frontend

# Rebuild after dependency changes
docker compose up --build
```

**Local development:**
```bash
# Terminal 1: Backend
cd backend
poetry run poe dev

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Worker (optional)
cd backend
poetry run poe serve worker
```

### Making Changes

**Backend changes:**
1. Make code changes in `backend/app/`
2. Create migration if models changed: `poetry run poe migration-generate "description"`
3. Apply migration: `poetry run poe migration-upgrade`
4. Test changes
5. Run pre-commit: `pre-commit run --all-files`
6. Commit

**Frontend changes:**
1. Make code changes in `frontend/src/`
2. Install new components: `npx shadcn-svelte@next add <component>`
3. Test changes
4. Run checks: `npm run lint && npm run check`
5. Commit (pre-commit runs automatically)

## Configuration Management

### Backend (EJSON)

```bash
# Edit unencrypted secrets
vim backend/secrets/development.json

# Encrypt for commit
cd backend
poetry run encrypt-ejson development

# Commit encrypted file
git add secrets/development.ejson
```

**Prefix conventions:**
- `_` = unencrypted (non-sensitive): `_HOST`, `_PORT`
- No prefix = encrypted (sensitive): `USER`, `PASSWORD`

### Frontend (Environment Variables)

```bash
# Create .env.development
echo 'PUBLIC_API_URL=http://localhost:8000/api' > frontend/.env.development
```

### Docker (EJSON Keys)

```yaml
# docker-compose.yaml
environment:
  - EJSON_PUBLIC_KEY=your-public-key
  - EJSON_PRIVATE_KEY=your-private-key
```

## Common Commands

### Backend

```bash
cd backend

# Development
poetry run poe dev                    # Start API server
poetry run poe serve worker           # Start Celery worker

# Database
poetry run poe migration-generate "description"
poetry run poe migration-upgrade

# Secrets
poetry run encrypt-ejson development
poetry run decrypt-ejson development

# Code quality
poetry run ruff check app/
poetry run ruff format app/
poetry run mypy app/
poetry run pytest
```

### Frontend

```bash
cd frontend

# Development
npm run dev                           # Start dev server
npm run build                         # Build for production

# Components
npx shadcn-svelte@next add button    # Add UI component

# Code quality
npm run lint                          # ESLint
npm run format                        # Prettier
npm run check                         # Type check
```

### Docker

```bash
# All services
docker compose up                     # Start all
docker compose up --build             # Rebuild and start
docker compose down                   # Stop all
docker compose down -v                # Stop and remove volumes

# Individual services
docker compose up -d postgres redis   # Just database and cache
docker compose restart api            # Restart API
docker compose logs -f frontend       # Follow frontend logs

# Shell access
docker compose exec api bash          # Backend shell
docker compose exec frontend sh       # Frontend shell
docker compose exec postgres psql -U app -d app_db  # Database shell

# Cleanup
docker compose down -v                # Remove volumes
docker system prune                   # Clean up Docker
```

### Monorepo

```bash
# Pre-commit
pre-commit install                    # Install hooks
pre-commit run --all-files           # Run all hooks

# Git
git status                           # Check status (respects .gitignore)
git add backend/ frontend/           # Add changes
git commit -m "feat: add feature"    # Commit (pre-commit runs)
```

## Adding New Features

### Backend Feature

1. **Create Model** (if needed)
   ```python
   # backend/app/domain/models.py
   class Post(TimeStampedModel, table=True):
       __tablename__ = "posts"
       title: str
       content: str
   ```

2. **Generate Migration**
   ```bash
   cd backend
   poetry run poe migration-generate "add posts table"
   poetry run poe migration-upgrade
   ```

3. **Create Repository**
   ```python
   # backend/app/domain/repository.py
   class PostRepository(Repository[Post]):
       model_class = Post
   ```

4. **Create Route**
   ```python
   # backend/app/api/routes/posts.py
   router = APIRouter(prefix="/posts", tags=["posts"])
   ```

5. **Register Route**
   ```python
   # backend/app/api/app.py
   from app.api.routes import posts
   api_router.include_router(posts.router)
   ```

### Frontend Feature

1. **Define Schema**
   ```typescript
   // frontend/src/lib/schemas/post.ts
   export const PostSchema = z.object({
       id: z.string(),
       title: z.string()
   });
   ```

2. **Create API Service**
   ```typescript
   // frontend/src/lib/api/posts.ts
   export async function getPosts(): Promise<Post[]> {
       return await api.get(ENDPOINTS.POSTS.LIST);
   }
   ```

3. **Create State Store**
   ```typescript
   // frontend/src/lib/state/posts.svelte.ts
   class PostsState {
       posts = $state<Post[]>([]);
       async fetch() { ... }
   }
   export const postsState = new PostsState();
   ```

4. **Create Route**
   ```svelte
   <!-- frontend/src/routes/(protected)/posts/+page.svelte -->
   <script lang="ts">
       import { postsState } from '$lib/state/posts.svelte';
   </script>
   ```

### Fullstack Feature (End-to-End)

Example: Adding a "Posts" feature

**Backend:**
1. Create Post model → Generate migration → Apply migration
2. Create PostRepository with CRUD methods
3. Create POST /api/posts, GET /api/posts routes
4. Add authentication: `user: User = Depends(current_user)`

**Frontend:**
1. Define PostSchema with Zod
2. Create `lib/api/posts.ts` service functions
3. Create `lib/state/posts.svelte.ts` state store
4. Add `routes/(protected)/posts/+page.svelte` with UI
5. Install needed components: `npx shadcn-svelte@next add card`

**Integration:**
1. Test API endpoints with curl or API docs
2. Test frontend with backend running
3. Verify authentication works end-to-end
4. Add error handling for network failures
5. Add loading states for better UX

## Debugging

### Backend Issues

```bash
# Check logs
docker compose logs api

# Database connection
docker compose exec postgres psql -U app -d app_db

# Check configuration
cd backend
poetry run python -c "from app.config import config; print(config().DATABASE)"

# Run migrations manually
docker compose exec api poetry run poe migration-upgrade
```

### Frontend Issues

```bash
# Check logs
docker compose logs frontend

# Check build
cd frontend
npm run build

# Type check
npm run check

# Browser DevTools
# - Network tab for API calls
# - Application tab for cookies
# - Console for errors
```

### Full Stack Issues

1. **Auth not working**
   - Check backend CORS settings allow frontend origin
   - Verify cookie settings: `SameSite=none`, `Secure=true`
   - Check `credentials: 'include'` in frontend fetch calls
   - Inspect cookies in browser DevTools

2. **API calls failing**
   - Check Caddy is routing correctly: `curl http://localhost:8080/api/health`
   - Verify backend is running: `docker compose ps`
   - Check CORS headers in network tab
   - Verify API base URL in frontend config

3. **Database issues**
   - Check migrations: `poetry run poe migration-current`
   - Verify connection: `docker compose exec postgres pg_isready`
   - Check credentials in secrets/development.json

## Documentation

- [Root Docs](docs/README.md) - Monorepo overview
- [Backend Docs](backend/docs/README.md) - Backend documentation
- [Backend CLAUDE.md](backend/CLAUDE.md) - Backend AI guidelines
- [Frontend Docs](frontend/docs/README.md) - Frontend documentation
- [Frontend CLAUDE.md](frontend/CLAUDE.md) - Frontend AI guidelines

## What NOT to Do

### Monorepo

- ❌ Don't add backend ignores to root .gitignore
- ❌ Don't add frontend ignores to root .gitignore
- ❌ Don't mix backend and frontend dependencies
- ❌ Don't skip pre-commit hooks

### Backend

- ❌ Don't commit secrets/*.json (decrypted)
- ❌ Don't manually edit migrations
- ❌ Don't bypass repository pattern
- ❌ Don't use "enhanced"/"extended" in names
- ❌ Don't import config directly in services - use dependency injection

### Frontend

- ❌ Don't use Tailwind v3 syntax
- ❌ Don't manually create shadcn components
- ❌ Don't forget base path in navigation
- ❌ Don't use `any` type - use type guards
- ❌ Don't forget `credentials: 'include'` in API calls

### Full Stack

- ❌ Don't hardcode API URLs (use environment variables)
- ❌ Don't store sensitive data in frontend
- ❌ Don't skip authentication on protected routes
- ❌ Don't forget to handle errors on both sides
- ❌ Don't commit without running pre-commit hooks

## Contributing

1. Read this CLAUDE.md and workspace-specific CLAUDE.md files
2. Follow the naming conventions (no "enhanced"/"extended")
3. Write type-safe code (Python type hints, TypeScript)
4. Add tests for new features
5. Run pre-commit hooks before committing
6. Write clear commit messages (conventional commits)
7. Update documentation when adding features

## Known Patterns

### Backend
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

### Frontend
```typescript
// Authentication
import { authState } from '$lib/state/auth.svelte';
if (authState.isAuthenticated) { ... }

// Navigation
import { goto } from '$app/navigation';
import { base } from '$app/paths';
await goto(`${base}/home`);

// API calls
import * as authApi from '$lib/api/auth';
const user = await authApi.getCurrentUser();

// Validation
import { LoginRequestSchema } from '$lib/schemas/auth';
const data = LoginRequestSchema.parse(input);
```

### Monorepo
```bash
# Backend
cd backend && poetry run poe dev
cd backend && poetry run poe migration-upgrade

# Frontend
cd frontend && npm run dev
cd frontend && npm run lint

# Docker
docker compose up
docker compose logs -f api

# Pre-commit
pre-commit run --all-files
```

## Personal Preferences & Project Gems

This section contains project-specific insights and preferences learned through development. Consider updating this section with key information for future reference.

### Naming & Terminology

1. **Avoid Generic Prefixes**
   - NEVER use: "enhanced", "extended", "improved", "new", "better", "advanced"
   - ALWAYS be specific about purpose and functionality
   - Examples:
     - ✅ `UserAuthenticationManager`, `PaymentProcessor`, `EmailNotificationService`
     - ❌ `EnhancedUserManager`, `ImprovedProcessor`, `NewService`

### Import Organization

**All imports must be at the top of the file** (after docstrings/comments):

```python
# Standard library imports
import asyncio
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Field, select

# Local imports
from app.infra.database.repository import Repository
from app.infra.monitoring.logging.logger import logger
from app.config import config
```

**TypeScript/Svelte imports:**

```typescript
// External libraries
import { goto } from '$app/navigation';
import { z } from 'zod';

// Internal modules
import { authState } from '$lib/state/auth.svelte';
import type { AuthUser } from '$lib/schemas/auth';

// Components
import { Button } from '$lib/components/ui/button';
```

### Code Organization Principles

1. **Separation of Concerns**
   - Backend: Repository → Service → Router pattern
   - Frontend: API Client → Service → State → Component pattern
   - Keep domain logic separate from infrastructure

2. **Type Safety First**
   - Python: Comprehensive type hints for all public functions
   - TypeScript: Strict mode with Zod runtime validation
   - Always include return type annotations (including `-> None`)

3. **Error Handling**
   - Use specific exception types, not generic exceptions
   - Log errors with structured logging (extra fields)
   - Provide user-friendly error messages in API responses

4. **Async Best Practices**
   - Backend: Use async/await throughout
   - Frontend: Proper loading and error states
   - Both: Handle race conditions and cleanup

### Documentation Philosophy

**Update this CLAUDE.md as you learn:**
- Add key architectural decisions
- Document non-obvious patterns
- Include gotchas and lessons learned
- Avoid littering with highly specific data
- Focus on reusable insights

### Testing Standards

- Write tests for new features (not optional)
- Test at the right level:
  - Unit: Business logic, utilities
  - Integration: API endpoints, database operations
  - E2E: Critical user flows
- Use fixtures and factories for test data
- Mock external dependencies

### Living Documentation

**Update this CLAUDE.md as you learn:**
- Add key architectural decisions made for this project
- Document non-obvious patterns discovered
- Include gotchas and lessons learned
- Avoid littering with highly specific implementation details
- Focus on reusable insights and principles
