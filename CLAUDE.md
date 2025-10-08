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
- Repository pattern with dependency injection

**Frontend:**
- SvelteKit 2.0 with Svelte 5
- Tailwind CSS v4
- shadcn-svelte UI components
- Cookie-based authentication
- Type-safe API client with Zod
- OpenAPI type generation from backend

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
   - FastAPI generates OpenAPI spec at `/openapi.json`

2. **Frontend in `/frontend/`**
   - Self-contained Node.js project with own dependencies
   - Has own .gitignore for Node-specific ignores
   - Generates TypeScript types from backend OpenAPI spec

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
   - Frontend: OpenAPI-generated types for compile-time safety

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
│   │   ├── api/           # HTTP layer (routes, middleware)
│   │   ├── auth/          # Authentication module
│   │   ├── infra/         # Infrastructure (DB, cache, logging)
│   │   ├── worker/        # Celery workers
│   │   ├── config.py      # Configuration management
│   │   └── di.py          # Dependency injection
│   ├── alembic/            # Database migrations
│   ├── scripts/            # Utility scripts
│   ├── secrets/            # EJSON configuration
│   ├── docs/               # Backend documentation
│   ├── pyproject.toml      # Python dependencies
│   └── .gitignore          # Python-specific ignores
│
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/           # API layer
│   │   │   │   ├── generated/  # OpenAPI-generated types
│   │   │   │   ├── client.ts   # Generic API client
│   │   │   │   ├── config.ts   # API configuration
│   │   │   │   └── auth.ts     # Auth service
│   │   │   ├── components/     # UI components
│   │   │   │   └── ui/        # shadcn-svelte components
│   │   │   ├── schemas/        # Zod validation schemas
│   │   │   ├── state/          # Global state management
│   │   │   └── utils/          # Utility functions
│   │   └── routes/        # File-based routing
│   │       ├── (protected)/   # Auth required
│   │       └── (public)/      # Public routes
│   ├── static/            # Static assets
│   ├── docs/              # Frontend documentation
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

## OpenAPI Type Generation

The frontend automatically generates TypeScript types from the backend's OpenAPI specification.

### How It Works

1. **Backend generates OpenAPI spec** at `http://localhost:8000/openapi.json`
2. **Frontend runs `npm run generate:api-types`** to create types
3. **Types are generated** to `frontend/src/lib/api/generated/schema.ts`
4. **Zod schemas reference** OpenAPI types for type safety

### Workflow

```bash
# After adding/modifying backend models:
cd frontend
npm run generate:api-types

# This creates/updates: src/lib/api/generated/schema.ts
```

### Usage Pattern

```typescript
// frontend/src/lib/schemas/auth.ts
import { z } from 'zod';
import type { components } from '$lib/api/generated/schema';

// Import OpenAPI type
type UserReadFromAPI = components['schemas']['UserRead'];

// Create Zod schema that matches
export const AuthUserSchema = z.object({
    id: z.string().uuid(),
    email: z.string().email(),
    full_name: z.string(),
    is_active: z.boolean(),
    is_verified: z.boolean(),
    is_superuser: z.boolean(),
    created_at: z.string().datetime()
});

export type AuthUser = z.infer<typeof AuthUserSchema>;

// Type-level check ensures alignment
// TypeScript will error if types diverge
const _check: AuthUser = {} as UserReadFromAPI;
const _reverseCheck: UserReadFromAPI = {} as AuthUser;
```

### Benefits

- ✅ Single source of truth (FastAPI backend schemas)
- ✅ Compile-time type safety in frontend
- ✅ Runtime validation with Zod
- ✅ Auto-completion in IDE
- ✅ Backend changes caught immediately by TypeScript
- ✅ No manual type duplication or drift

### Generated Types Structure

```typescript
// frontend/src/lib/api/generated/schema.ts

export interface paths {
    "/api/auth/users/me": {
        get: operations["users_current_user"];
        patch: operations["users_patch_current_user"];
    };
    "/api/todos": {
        get: operations["list_todos"];
        post: operations["create_todo"];
    };
}

export interface components {
    schemas: {
        UserRead: {
            id: string;
            email: string;
            full_name: string;
            // ...
        };
        TodoRead: {
            id: string;
            title: string;
            completed: boolean;
            // ...
        };
    };
}

export interface operations {
    users_current_user: {
        responses: {
            200: {
                content: {
                    "application/json": components["schemas"]["UserRead"];
                };
            };
        };
    };
}
```

## Backend Development

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

3. **EJSON management commands**
   ```bash
   cd backend
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
   cd backend
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
   - `BaseModel` - UUID primary key + timestamps
   - `TimeStampedModel` - Adds created_at, updated_at
   - `AuditableModel` - Adds created_by_id, updated_by_id
   - `SoftDeleteModel` - Adds deleted_at, deleted_by_id

### Backend Code Style

1. **Import organization**
   ```python
   # Standard library
   import os
   from typing import Optional
   from uuid import UUID

   # Third party
   from fastapi import APIRouter
   from sqlmodel import Field

   # Local
   from app.config import config
   from app.auth.models import User
   ```

2. **Type hints required**
   - All function signatures must have type hints
   - Use `Optional[T]` or `T | None` for nullable types
   - Repository methods use Generic types
   - Always include return type annotations (including `-> None`)

3. **Ruff linting standards**
   - Minimize use of `noqa` comments - fix issues properly
   - Only use `noqa` for legitimate cases:
     - `ARG002`: Unused arguments required by parent class/interface
     - `C901`: Complex functions with justified linear flow
   - Exception handling:
     - Use `logger.exception("message")` without `str(e)` - includes traceback
     - Add `from e` or `from None` to raise statements
   - Prefer ternary operators for simple if-else assignments

### Repository Pattern

```python
from app.infra.database.repository import Repository
from app.auth.models import User

class UserRepository(Repository[User]):
    model_class = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.find_one_by_attributes(email=email)

# Available methods on all repositories:
await repo.get_by_id(id)
await repo.find_by_attributes(**kwargs)
await repo.find_one_by_attributes(**kwargs)
await repo.create(obj)
await repo.update(obj)
await repo.delete(obj)
await repo.paginate(page=1, page_size=50)
await repo.search(search_term, search_fields)
```

### API Development

```python
from fastapi import APIRouter, Depends
from app.auth.dependencies import current_active_user
from app.auth.models import User

router = APIRouter(prefix="/todos", tags=["todos"])

@router.get("/")
async def list_todos(user: User = Depends(current_active_user)):
    """List todos for current user."""
    # Implementation
    pass

# Register in app/api/app.py:
from app.api.routes import todos
api_router.include_router(todos.router)
```

## Frontend Development

### Component & Styling

1. **Tailwind CSS v4 syntax**
   - Use `@import "tailwindcss";` (NOT `@tailwind base;`)
   - Use `@theme inline { }` directive to expose CSS variables
   - Wrap CSS variable values with `hsl()`: `--background: hsl(0 0% 100%);`
   - Add Tailwind plugin to vite.config.ts: `import tailwindcss from '@tailwindcss/vite'`

2. **shadcn-svelte components**
   - ALWAYS use CLI to install components: `npx shadcn-svelte@next add <component>`
   - NEVER manually create component files
   - Components follow compound pattern (e.g., Card.Root, Card.Header, Card.Content)

3. **Component conventions**
   - File naming: PascalCase for components (e.g., `LoginForm.svelte`)
   - Use `$props()` for component props (Svelte 5)
   - Use `{@render children?.()}` for slot content
   - Keep components focused and composable

### State Management (Svelte 5 Runes)

```typescript
// lib/state/auth.svelte.ts
class AuthState {
    user = $state<AuthUser | null>(null);
    loading = $state(false);

    // Derived state
    isAuthenticated = $derived(this.user !== null);

    async login(email: string, password: string) {
        this.loading = true;
        try {
            // ... implementation
        } finally {
            this.loading = false;
        }
    }
}

export const authState = new AuthState();
```

### API Integration

```typescript
// lib/api/config.ts
export const API_BASE_URL = PUBLIC_API_URL || `${base}/api`;
export const ENDPOINTS = {
    AUTH: {
        LOGIN: '/auth/cookie/login',
        LOGOUT: '/auth/cookie/logout',
        ME: '/auth/users/me'
    },
    TODOS: {
        LIST: '/todos',
        CREATE: '/todos'
    }
} as const;

// lib/api/todos.ts
import * as api from './client';
import { ENDPOINTS } from './config';
import type { components } from './generated/schema';

type TodoResponse = components['schemas']['TodoRead'];

export async function getTodos(): Promise<TodoResponse[]> {
    return await api.get(ENDPOINTS.TODOS.LIST);
}
```

### Routing & Navigation

1. **Base path handling**
   - ALWAYS use `{base}/path` in templates
   - ALWAYS use `${base}/path` in goto() calls
   - Set base in svelte.config.js: `kit: { paths: { base: '/app' } }`

2. **Route groups**
   - `(protected)` - Requires authentication
   - `(public)` - No authentication required
   - Use `+layout.svelte` for auth guards

3. **Auth guard pattern**
   ```svelte
   <script lang="ts">
       import { authState } from '$lib/state/auth.svelte';
       import { goto } from '$app/navigation';
       import { base } from '$app/paths';
       import { browser } from '$app/environment';

       $effect(() => {
           if (browser && !authState.loading && !authState.isAuthenticated) {
               goto(`${base}/login`);
           }
       });
   </script>

   {#if authState.isAuthenticated}
       {@render children?.()}
   {/if}
   ```

### Frontend Code Style

1. **TypeScript**
   - Strict mode enabled
   - Use Zod schemas for runtime validation
   - Type inference from schemas: `type AuthUser = z.infer<typeof AuthUserSchema>`
   - Reference OpenAPI types for type safety
   - Explicit return types for public APIs

2. **Error handling**
   - Use type guards instead of `any`:
     ```typescript
     catch (error) {
         if (error && typeof error === 'object' && 'status' in error) {
             // Handle API error
         } else if (error instanceof Error) {
             // Handle Error
         }
     }
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
- OpenAPI Spec: `http://localhost:8000/openapi.json`

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

### Adding New Features (End-to-End)

Example: Adding a "Todos" feature

**Backend (in `/backend/`):**

1. **Create Model**
   ```python
   # app/domain/models.py
   from app.infra.database.models import TimeStampedModel
   from sqlmodel import Field
   import uuid

   class Todo(TimeStampedModel, table=True):
       __tablename__ = "todos"

       id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
       title: str
       completed: bool = Field(default=False)
       user_id: uuid.UUID = Field(foreign_key="users.id")
   ```

2. **Create Pydantic Schemas**
   ```python
   # Same file or separate schemas.py
   from pydantic import BaseModel
   import uuid
   from datetime import datetime

   class TodoCreate(BaseModel):
       title: str

   class TodoUpdate(BaseModel):
       title: str | None = None
       completed: bool | None = None

   class TodoRead(BaseModel):
       id: uuid.UUID
       title: str
       completed: bool
       user_id: uuid.UUID
       created_at: datetime
       updated_at: datetime

       model_config = ConfigDict(from_attributes=True)
   ```

3. **Create Repository**
   ```python
   # app/domain/repository.py
   from app.infra.database.repository import Repository

   class TodoRepository(Repository[Todo]):
       model_class = Todo

       async def get_by_user(self, user_id: uuid.UUID):
           return await self.find_by_attributes(user_id=user_id)
   ```

4. **Create Router**
   ```python
   # app/api/routes/todos.py
   from fastapi import APIRouter, Depends
   from app.auth.dependencies import current_active_user
   from app.auth.models import User

   router = APIRouter(prefix="/todos", tags=["todos"])

   @router.get("/", response_model=list[TodoRead])
   async def list_todos(user: User = Depends(current_active_user)):
       # Implementation
       pass

   @router.post("/", response_model=TodoRead, status_code=201)
   async def create_todo(
       todo: TodoCreate,
       user: User = Depends(current_active_user)
   ):
       # Implementation
       pass
   ```

5. **Register Router**
   ```python
   # app/api/app.py
   from app.api.routes import todos
   api_router.include_router(todos.router)
   ```

6. **Register Model in Alembic**
   ```python
   # alembic/env.py
   with suppress(ImportError):
       from app.auth import models as auth_models
       from app.domain import models as domain_models  # Add this
   ```

7. **Generate & Run Migration**
   ```bash
   poetry run poe migration-generate "add todos table"
   poetry run poe migration-upgrade
   ```

**Frontend (in `/frontend/`):**

1. **Generate Types from OpenAPI**
   ```bash
   npm run generate:api-types
   ```

2. **Create Zod Schema with OpenAPI Types**
   ```typescript
   // src/lib/schemas/todo.ts
   import { z } from 'zod';
   import type { components } from '$lib/api/generated/schema';

   type TodoFromAPI = components['schemas']['TodoRead'];

   export const TodoSchema = z.object({
       id: z.string().uuid(),
       title: z.string(),
       completed: z.boolean(),
       user_id: z.string().uuid(),
       created_at: z.string().datetime(),
       updated_at: z.string().datetime()
   });

   export type Todo = z.infer<typeof TodoSchema>;

   // Type check
   const _check: Todo = {} as TodoFromAPI;
   ```

3. **Add Endpoints**
   ```typescript
   // src/lib/api/config.ts
   export const ENDPOINTS = {
       // ... existing endpoints
       TODOS: {
           LIST: '/todos',
           CREATE: '/todos'
       }
   } as const;
   ```

4. **Create API Service**
   ```typescript
   // src/lib/api/todos.ts
   import * as api from './client';
   import { ENDPOINTS } from './config';
   import { TodoSchema } from '$lib/schemas/todo';
   import type { Todo } from '$lib/schemas/todo';
   import { z } from 'zod';

   export async function getTodos(): Promise<Todo[]> {
       const response = await api.get(ENDPOINTS.TODOS.LIST);
       return z.array(TodoSchema).parse(response);
   }

   export async function createTodo(title: string): Promise<Todo> {
       const response = await api.post(ENDPOINTS.TODOS.CREATE, { title });
       return TodoSchema.parse(response);
   }
   ```

5. **Create State Store**
   ```typescript
   // src/lib/state/todos.svelte.ts
   import * as todosApi from '$lib/api/todos';
   import type { Todo } from '$lib/schemas/todo';

   class TodosState {
       todos = $state<Todo[]>([]);
       loading = $state(false);
       error = $state<string | null>(null);

       async fetch() {
           this.loading = true;
           this.error = null;
           try {
               this.todos = await todosApi.getTodos();
           } catch (e) {
               this.error = e instanceof Error ? e.message : 'Failed to load todos';
           } finally {
               this.loading = false;
           }
       }

       async create(title: string) {
           const todo = await todosApi.createTodo(title);
           this.todos = [...this.todos, todo];
       }
   }

   export const todosState = new TodosState();
   ```

6. **Create Page Component**
   ```svelte
   <!-- src/routes/(protected)/todos/+page.svelte -->
   <script lang="ts">
       import { todosState } from '$lib/state/todos.svelte';
       import { onMount } from 'svelte';
       import * as Card from '$lib/components/ui/card';
       import { Button } from '$lib/components/ui/button';

       onMount(() => {
           todosState.fetch();
       });
   </script>

   <div class="container mx-auto p-6">
       {#if todosState.loading}
           <p>Loading...</p>
       {:else if todosState.error}
           <p class="text-destructive">{todosState.error}</p>
       {:else}
           {#each todosState.todos as todo}
               <Card.Root>
                   <Card.Header>
                       <Card.Title>{todo.title}</Card.Title>
                   </Card.Header>
               </Card.Root>
           {/each}
       {/if}
   </div>
   ```

## Common Commands

### Monorepo

```bash
# Pre-commit
pre-commit install                    # Install hooks
pre-commit run --all-files           # Run all hooks

# Git
git status                           # Check status
git add backend/ frontend/           # Add changes
git commit -m "feat: add feature"    # Commit (pre-commit runs)
```

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

# Type generation
npm run generate:api-types            # Generate types from OpenAPI spec

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

# Individual services
docker compose up -d postgres redis   # Just database and cache
docker compose restart api            # Restart API
docker compose logs -f frontend       # Follow frontend logs

# Shell access
docker compose exec api bash          # Backend shell
docker compose exec frontend sh       # Frontend shell

# Cleanup
docker compose down -v                # Remove volumes
docker system prune                   # Clean up Docker
```

## Debugging

### Backend Issues

```bash
# Check logs
docker compose logs api

# Database connection
docker compose exec postgres psql -U app -d app_db

# Check migrations
cd backend
poetry run poe migration-current
```

### Frontend Issues

```bash
# Check logs
docker compose logs frontend

# Type check
cd frontend
npm run check

# Browser DevTools
# - Network tab for API calls
# - Application tab for cookies
# - Console for errors
```

### OpenAPI Type Generation Issues

```bash
# Ensure backend is running
curl http://localhost:8000/openapi.json

# Regenerate types
cd frontend
npm run generate:api-types

# Check generated file
cat src/lib/api/generated/schema.ts
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

3. **Type mismatches**
   - Regenerate types: `npm run generate:api-types`
   - Check Zod schemas match OpenAPI types
   - Review type-check comments in schema files

## Documentation

- [Root Docs](docs/README.md) - Monorepo overview
- [Backend Docs](backend/docs/README.md) - Backend documentation
- [Frontend Docs](frontend/docs/README.md) - Frontend documentation

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
- ❌ Don't manually create types that exist in OpenAPI spec

### Full Stack

- ❌ Don't hardcode API URLs (use environment variables)
- ❌ Don't store sensitive data in frontend
- ❌ Don't skip authentication on protected routes
- ❌ Don't forget to regenerate types after backend changes
- ❌ Don't commit without running pre-commit hooks

## Known Patterns

### Backend
```python
# Repository Pattern
from app.infra.database.repository import Repository

class UserRepository(Repository[User]):
    model_class = User

# Dependency Injection (FastAPI)
from fastapi import Depends
from app.auth.dependencies import current_active_user

@router.get("/protected")
async def endpoint(user: User = Depends(current_active_user)):
    ...

# Logging
from app.infra.monitoring.logging.logger import logger
logger.info("User created", extra={"user_id": str(user.id)})
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

// API calls with OpenAPI types
import type { components } from '$lib/api/generated/schema';
import * as api from '$lib/api/client';

type UserResponse = components['schemas']['UserRead'];
const user: UserResponse = await api.get('/auth/users/me');

// Validation
import { LoginRequestSchema } from '$lib/schemas/auth';
const data = LoginRequestSchema.parse(input);
```

## Contributing

1. Read this CLAUDE.md thoroughly
2. Follow the naming conventions (no "enhanced"/"extended")
3. Write type-safe code (Python type hints, TypeScript)
4. Regenerate frontend types after backend schema changes
5. Add tests for new features
6. Run pre-commit hooks before committing
7. Write clear commit messages (conventional commits)
8. Update documentation when adding features

## Personal Preferences & Project Gems

This section contains project-specific insights and preferences learned through development.

### Import Organization

**All imports must be at the top of the file** (after docstrings/comments):

```python
# Standard library imports
import asyncio
from typing import Optional, List

# Third-party imports
from fastapi import APIRouter, Depends
from sqlmodel import Field

# Local imports
from app.infra.database.repository import Repository
from app.config import config
```

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
   - Frontend: Use OpenAPI-generated types
   - Always include return type annotations

3. **Error Handling**
   - Use specific exception types, not generic exceptions
   - Log errors with structured logging (extra fields)
   - Provide user-friendly error messages in API responses

### Documentation Philosophy

**Update this CLAUDE.md as you learn:**
- Add key architectural decisions
- Document non-obvious patterns
- Include gotchas and lessons learned
- Focus on reusable insights and principles
