# Fullstack Boilerplate Documentation

Production-ready fullstack monorepo with FastAPI backend and SvelteKit frontend.

## Documentation Structure

### Monorepo Docs
- [Getting Started](./01-getting-started.md) - Initial setup and quickstart
- [Architecture](./02-architecture.md) - System architecture and design patterns
- [Docker Setup](./03-docker.md) - Container orchestration and deployment

### Backend Docs
- [Backend Documentation](../backend/docs/README.md) - Complete backend documentation

### Frontend Docs
- [Frontend Documentation](../frontend/docs/README.md) - Complete frontend documentation

### AI Assistant Guidelines
- [Root CLAUDE.md](../CLAUDE.md) - Comprehensive AI development guidelines for both backend and frontend

## Quick Start

```bash
# 1. Setup backend
cd backend
poetry install
cp secrets/local.json.example secrets/local.json
# Edit secrets/local.json

# 2. Setup frontend
cd ../frontend
npm install

# 3. Start all services with Docker
cd ..
docker compose up
```

**Access:**
- Frontend: `http://localhost:8080/app`
- Backend API: `http://localhost:8080/api`
- API Docs: `http://localhost:8080/api/docs`

## Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── alembic/            # Database migrations
│   ├── scripts/            # Utility scripts
│   ├── secrets/            # EJSON secrets
│   ├── docs/               # Backend documentation
│   └── pyproject.toml      # Python dependencies
│
├── frontend/               # SvelteKit frontend
│   ├── src/                # Source code
│   ├── static/             # Static assets
│   ├── docs/               # Frontend documentation
│   └── package.json        # Node dependencies
│
├── docs/                   # Monorepo documentation (you are here)
├── Caddyfile              # Reverse proxy configuration
├── docker-compose.yaml    # Docker orchestration
└── CLAUDE.md              # Root AI guidelines
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLModel ORM
- **Migrations**: Alembic
- **Workers**: Celery with Redis
- **Auth**: FastAPI Users (JWT bearer + cookie)
- **Secrets**: EJSON encryption
- **Deployment**: Docker multi-stage builds

### Frontend
- **Framework**: SvelteKit 2.0
- **UI Library**: Svelte 5 (runes system)
- **Styling**: Tailwind CSS v4
- **Components**: shadcn-svelte
- **Auth**: Cookie-based (HttpOnly)
- **Validation**: Zod with TypeScript
- **Build**: Vite

### Infrastructure
- **Reverse Proxy**: Caddy
- **Orchestration**: Docker Compose
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Code Quality**: Pre-commit hooks (Ruff, ESLint, Prettier)

## Key Features

- **Full-stack TypeScript/Python** - End-to-end type safety
- **Cookie-based Authentication** - Secure, HttpOnly cookies
- **Repository Pattern** - Clean data access layer
- **State Management** - Svelte 5 runes with singleton stores
- **API Client** - Type-safe with Zod validation
- **Database Migrations** - Auto-generated with Alembic
- **Background Workers** - Celery task queue
- **Encrypted Secrets** - EJSON with prefix conventions
- **Docker Development** - Hot-reload in containers
- **Code Quality** - Comprehensive linting and formatting

## Resources

- [Root CLAUDE.md](../CLAUDE.md) - AI assistant guidelines
- [Backend Docs](../backend/docs/README.md) - Backend documentation
- [Frontend Docs](../frontend/docs/README.md) - Frontend documentation
