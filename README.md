# Full Stack Boilerplate

A modern full-stack application boilerplate with FastAPI backend and SvelteKit frontend.

## Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database
- **Redis** - Cache and message broker
- **Celery** - Async task queue
- **Alembic** - Database migrations
- **Poetry** - Dependency management

### Frontend
- **SvelteKit** - Modern web framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn-svelte** - UI components (bits-ui)

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **ngrok** - Tunneling for webhooks and external access

## Project Structure

```
.
├── backend/          # FastAPI backend
├── frontend/         # SvelteKit frontend
├── docker-compose.yaml
├── ngrok.yml         # ngrok configuration
└── dockerdata/       # Docker volumes (gitignored)
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)
- ngrok account (free tier works) - https://ngrok.com

### Running with Docker Compose

1. Start all services:
```bash
docker compose up
```

2. Access the application via Caddy (recommended):
- **App (via Caddy)**: http://localhost:8080
- **API (via Caddy)**: http://localhost:8080/api
- **API Docs**: http://localhost:8080/api/docs

Or access services directly:
- Frontend (direct): http://localhost:5173
- Backend API (direct): http://localhost:8000

**Architecture:**
```
          ┌─────────────┐
          │   Caddy     │  :8080
          │   Proxy     │
          └──────┬──────┘
                 │
        ┌────────┴────────┐
        │                 │
    /api/*           everything else
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────┐
   │Backend  │      │Frontend  │
   │FastAPI  │:8000 │SvelteKit │:5173
   └─────────┘      └──────────┘
```

### Exposing with ngrok (for webhooks, mobile testing, etc.)

1. Install ngrok:
```bash
brew install ngrok  # macOS
# or download from https://ngrok.com/download
```

2. Set your ngrok auth token in `ngrok.yml`:
```yaml
authtoken: YOUR_NGROK_AUTH_TOKEN
```

3. Start ngrok tunnel pointing to Caddy:
```bash
ngrok http 8080 --config ngrok.yml
```

This creates one tunnel that routes everything:
- **App**: https://xxx.ngrok-free.app → Frontend (via Caddy)
- **API**: https://xxx.ngrok-free.app/api → Backend (via Caddy)

4. Add your ngrok domain to `frontend/vite.config.ts`:
```typescript
allowedHosts: [
  "xxx.ngrok-free.app"  // Your ngrok domain
]
```

Now your entire app (frontend + API) is accessible via one ngrok URL!

### Local Development

#### Backend
```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Features

- ✅ User authentication (JWT)
- ✅ Database migrations with Alembic
- ✅ Async task processing with Celery
- ✅ Modern UI with shadcn-svelte
- ✅ Type-safe frontend and backend
- ✅ Docker development environment
- ✅ ngrok integration for webhooks and external access

## License

MIT
