# Python Backend Boilerplate Documentation

Production-ready FastAPI backend with authentication, database management, and Docker deployment.

## Documentation Structure

- [Getting Started](./01-getting-started.md) - Initial setup and first steps
- [Configuration](./02-configuration.md) - Environment variables and secrets management
- [Database](./03-database.md) - Database setup, migrations, and patterns
- [Authentication](./04-authentication.md) - User authentication and authorization
- [Docker & Deployment](./05-docker-deployment.md) - Containerization and deployment
- [Development](./06-development.md) - Development workflow and best practices
- [Architecture](./07-architecture.md) - System architecture and design patterns

## Quick Start

```bash
# Install dependencies
poetry install

# Setup secrets
cp secrets/local.json.example secrets/local.json
# Edit secrets/local.json with your configuration

# Run migrations
poetry run poe migration-upgrade

# Start development server
poetry run poe dev

# Or use Docker
docker compose up
```

## Key Features

- **FastAPI** - Modern async web framework
- **SQLModel** - Type-safe database models
- **FastAPI Users** - Complete authentication system
- **Alembic** - Database migration management
- **Celery** - Async task queue
- **EJSON** - Encrypted secrets management
- **Docker** - Container orchestration
- **Dependency Injection** - Clean architecture patterns

## Project Structure

```
app/
├── api/              # HTTP API layer
│   ├── middleware/   # Security, CORS, rate limiting
│   └── routes/       # API endpoints
├── auth/             # Authentication module
│   ├── password/     # Password-based auth
│   ├── models.py     # User models
│   └── dependencies.py
├── infra/            # Infrastructure layer
│   ├── database/     # Database setup
│   ├── monitoring/   # Logging, tracing
│   └── cache/        # Redis caching
├── worker/           # Celery workers
└── config.py         # Configuration management

alembic/              # Database migrations
scripts/              # Utility scripts
secrets/              # Encrypted configuration
```

## Environment Support

- **development** - Local development with hot reload
- **staging** - Pre-production testing
- **production** - Production deployment

Each environment has its own EJSON file in `secrets/`.
