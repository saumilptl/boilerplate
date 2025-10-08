# Frontend Documentation

Modern SvelteKit frontend with Tailwind CSS v4, shadcn-svelte components, and cookie-based authentication.

## Documentation Structure

- [Getting Started](./01-getting-started.md) - Setup and installation
- [Routing & Navigation](./02-routing-navigation.md) - File-based routing and base paths
- [State Management](./03-state-management.md) - Svelte 5 runes and stores
- [API Integration](./04-api-integration.md) - HTTP client and service layer
- [Authentication](./05-authentication.md) - Cookie-based auth flow
- [Styling & Components](./06-styling-components.md) - Tailwind v4 and shadcn-svelte
- [Development Workflow](./07-development.md) - Best practices and tools

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Key Features

- **SvelteKit 2.0** - Modern meta-framework with file-based routing
- **Svelte 5** - Latest version with runes system for reactivity
- **Tailwind CSS v4** - Latest CSS framework with new syntax
- **shadcn-svelte** - High-quality UI component library
- **Cookie-based Auth** - Secure authentication with HttpOnly cookies
- **Type Safety** - TypeScript with Zod runtime validation
- **Code Quality** - ESLint, Prettier, and pre-commit hooks

## Project Structure

```
src/
├── lib/
│   ├── api/              # API client and services
│   ├── components/ui/    # shadcn-svelte components
│   ├── schemas/          # Zod validation schemas
│   ├── state/            # Global state stores
│   └── utils/            # Utility functions
└── routes/
    ├── (protected)/      # Auth-required routes
    └── (public)/         # Public routes
```

## Technology Stack

- **Framework**: SvelteKit 2.0
- **UI Library**: Svelte 5
- **Styling**: Tailwind CSS v4
- **Components**: shadcn-svelte (bits-ui)
- **Validation**: Zod
- **Type Checking**: TypeScript
- **Code Quality**: ESLint, Prettier
- **Build Tool**: Vite
