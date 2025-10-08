# Claude Development Guidelines - Frontend

This document provides context for AI assistants working on the frontend codebase.

## Project Overview

SvelteKit 2.0 frontend with:
- Svelte 5 (latest runes system)
- Tailwind CSS v4
- shadcn-svelte UI components
- Cookie-based authentication
- Type-safe API client with Zod validation
- Form handling with validation

## Critical Rules

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
   - Use `npx shadcn-svelte@next init` for initial setup

3. **Component conventions**
   - File naming: PascalCase for components (e.g., `LoginForm.svelte`)
   - Use `$props()` for component props (Svelte 5)
   - Use `{@render children?.()}` for slot content
   - Keep components focused and composable

### State Management

1. **Svelte 5 runes**
   - Use `$state()` for reactive values
   - Use `$derived()` for computed values
   - Use `$effect()` for side effects
   - Use singleton class pattern for global stores

2. **State store pattern**
   ```typescript
   class AuthState {
       user = $state<AuthUser | null>(null);
       loading = $state(false);

       isAuthenticated = $derived(this.user !== null);

       async login(email: string, password: string) {
           this.loading = true;
           // ... implementation
       }
   }

   export const authState = new AuthState();
   ```

3. **State files**
   - Name with `.svelte.ts` extension
   - Export singleton instance
   - Keep state granular and focused

### API & Data Fetching

1. **API client pattern**
   - Generic client in `lib/api/client.ts`
   - Service modules for specific domains (e.g., `lib/api/auth.ts`)
   - Always use Zod schemas for validation
   - Include credentials for cookie auth: `credentials: 'include'`

2. **API configuration**
   ```typescript
   export const API_BASE_URL = PUBLIC_API_URL || `${base}/api`;
   export const ENDPOINTS = {
       AUTH: {
           LOGIN: '/auth/cookie/login',
           LOGOUT: '/auth/cookie/logout',
           ME: '/auth/users/me'
       }
   } as const;
   ```

3. **Form encoding for login**
   - Login uses `application/x-www-form-urlencoded`
   - Use URLSearchParams for encoding
   - Other endpoints use JSON

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
   {:else if authState.loading}
       <!-- Loading state -->
   {/if}
   ```

### Code Style & Quality

1. **TypeScript**
   - Strict mode enabled
   - Use Zod schemas for runtime validation
   - Type inference from schemas: `type AuthUser = z.infer<typeof AuthUserSchema>`
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
   - User-friendly error messages in state
   - Log errors to console for debugging

3. **Naming conventions**
   - NEVER use "enhanced", "extended", "improved" in names
   - Be specific: `UserProfileForm` not `EnhancedForm`
   - Components: PascalCase
   - Utilities: kebab-case
   - State stores: kebab-case with `.svelte.ts`

4. **ESLint/Prettier standards**
   - Minimize disable comments - fix issues properly
   - Only disable rules when justified:
     - `svelte/no-navigation-without-resolve` - When using base path correctly
     - `svelte/prefer-svelte-reactivity` - For non-reactive data (URLSearchParams)
   - Use tabs for indentation
   - Single quotes for strings
   - No trailing commas

5. **Pre-commit hooks**
   - All code must pass pre-commit hooks before committing
   - Run `npm run lint` and `npm run format` before commit
   - Hooks include: Prettier, ESLint

### Authentication

1. **Cookie-based auth**
   - JWT stored in HttpOnly cookies
   - Backend sets cookie with `SameSite=none` and `Secure=true`
   - Frontend uses `credentials: 'include'` in fetch calls
   - No manual token management needed

2. **Auth flow**
   ```typescript
   // 1. Login with form encoding
   const formData = new URLSearchParams();
   formData.append('username', email);
   formData.append('password', password);

   await fetch(`${API_BASE_URL}/auth/cookie/login`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
       body: formData,
       credentials: 'include'
   });

   // 2. Fetch user (cookie sent automatically)
   await authState.fetchUser();

   // 3. Redirect to protected route
   await goto(`${base}/home`);
   ```

3. **Auth initialization**
   - Fetch user in root `+layout.ts`
   - Disable SSR: `export const ssr = false;`
   - Handle auth failures gracefully

## Project Structure

```
src/
├── app.html              # HTML template
├── app.css              # Global styles with Tailwind
├── app.d.ts             # TypeScript declarations
├── lib/
│   ├── api/            # API layer
│   │   ├── client.ts       # Generic API client
│   │   ├── config.ts       # API configuration
│   │   └── auth.ts         # Auth service
│   ├── components/     # UI components
│   │   └── ui/            # shadcn-svelte components
│   ├── schemas/        # Zod validation schemas
│   │   └── auth.ts         # Auth schemas
│   ├── state/          # Global state management
│   │   └── auth.svelte.ts  # Auth state
│   └── utils/          # Utility functions
└── routes/             # File-based routing
    ├── +layout.ts          # Root layout load
    ├── +layout.svelte      # Root layout
    ├── +page.svelte        # Root redirect
    ├── (protected)/        # Auth required
    │   ├── +layout.svelte  # Auth guard
    │   └── home/
    │       └── +page.svelte
    └── (public)/           # Public routes
        ├── login/
        │   └── +page.svelte
        └── signup/
            └── +page.svelte
```

## Architecture Patterns

### Separation of Concerns

```
API Client → Services → Schemas → State Management → UI Components
```

1. **API Client** - Generic HTTP client
2. **Services** - Domain-specific API functions
3. **Schemas** - Zod validation and type inference
4. **State Management** - Reactive state with Svelte 5 runes
5. **UI Components** - Presentation layer

### Data Flow

```
User Action → Component → State Store → Service → API Client → Backend
                ↑                                                  ↓
                └──────── State Update ← Response ← ←─────────────┘
```

## Common Commands

```bash
# Development
npm run dev              # Start dev server
npm run build            # Build for production
npm run preview          # Preview production build

# Code Quality
npm run lint             # Run ESLint
npm run format           # Format with Prettier
npm run check            # Type check with svelte-check

# Dependencies
npm install <package>    # Add dependency
npx shadcn-svelte@next add <component>  # Add UI component
```

## Adding New Features

### 1. Create API Endpoint Integration

```typescript
// lib/api/config.ts - Add endpoint
export const ENDPOINTS = {
    POSTS: {
        LIST: '/posts',
        CREATE: '/posts',
        GET: '/posts/:id'
    }
} as const;

// lib/schemas/post.ts - Define schema
export const PostSchema = z.object({
    id: z.string(),
    title: z.string(),
    content: z.string()
});
export type Post = z.infer<typeof PostSchema>;

// lib/api/posts.ts - Create service
export async function getPosts(): Promise<Post[]> {
    const response = await api.get(ENDPOINTS.POSTS.LIST);
    return z.array(PostSchema).parse(response);
}
```

### 2. Create State Store

```typescript
// lib/state/posts.svelte.ts
class PostsState {
    posts = $state<Post[]>([]);
    loading = $state(false);
    error = $state<string | null>(null);

    async fetchPosts() {
        this.loading = true;
        try {
            this.posts = await getPosts();
        } catch (error) {
            this.error = 'Failed to load posts';
        } finally {
            this.loading = false;
        }
    }
}

export const postsState = new PostsState();
```

### 3. Create Component

```svelte
<!-- routes/(protected)/posts/+page.svelte -->
<script lang="ts">
    import { postsState } from '$lib/state/posts.svelte';
    import { onMount } from 'svelte';
    import * as Card from '$lib/components/ui/card';

    onMount(() => {
        postsState.fetchPosts();
    });
</script>

{#if postsState.loading}
    <p>Loading...</p>
{:else if postsState.error}
    <p class="text-destructive">{postsState.error}</p>
{:else}
    {#each postsState.posts as post}
        <Card.Root>
            <Card.Header>
                <Card.Title>{post.title}</Card.Title>
            </Card.Header>
            <Card.Content>
                {post.content}
            </Card.Content>
        </Card.Root>
    {/each}
{/if}
```

## Environment Variables

- `PUBLIC_API_URL` - Backend API URL (optional, defaults to `/api`)
- Environment-specific variables in `.env.development`, `.env.production`

## Debugging Tips

1. **Auth issues**
   - Check browser DevTools → Application → Cookies for `auth-token`
   - Verify CORS settings in backend
   - Check `credentials: 'include'` in fetch calls

2. **Routing issues**
   - Verify all paths use `{base}` or `${base}` prefix
   - Check svelte.config.js for correct base path
   - Use browser DevTools → Network to see redirects

3. **Styling not working**
   - Verify `@import "tailwindcss";` in app.css
   - Check `@theme inline` directive exists
   - Ensure `@tailwindcss/vite` plugin in vite.config.ts
   - Verify CSS variables wrapped with `hsl()`

4. **Type errors**
   - Run `npm run check` for detailed errors
   - Verify Zod schemas match API response
   - Check TypeScript strict mode settings

## Documentation

Full documentation in `docs/`:
- [Getting Started](docs/01-getting-started.md)
- [Routing & Navigation](docs/02-routing-navigation.md)
- [State Management](docs/03-state-management.md)
- [API Integration](docs/04-api-integration.md)
- [Authentication](docs/05-authentication.md)
- [Styling & Components](docs/06-styling-components.md)
- [Development Workflow](docs/07-development.md)

## Known Patterns

```typescript
// Authentication state
import { authState } from '$lib/state/auth.svelte';

if (authState.isAuthenticated) {
    console.log(authState.user?.email);
}

await authState.login(email, password);

// Navigation with base path
import { goto } from '$app/navigation';
import { base } from '$app/paths';

// ALWAYS use base prefix
await goto(`${base}/home`);

// In templates
<a href="{base}/profile">Profile</a>

// API calls through service layer
import * as authApi from '$lib/api/auth';

const user = await authApi.getCurrentUser();
await authApi.logout();

// Validation with Zod
import { LoginRequestSchema } from '$lib/schemas/auth';
import type { LoginRequest } from '$lib/schemas/auth';

const validated = LoginRequestSchema.parse(formData);
// Type is inferred: LoginRequest

// State management pattern
import { MyState } from '$lib/state/my-state.svelte';

class MyState {
    data = $state<Data[]>([]);
    loading = $state(false);

    // Derived state
    count = $derived(this.data.length);

    async fetch() {
        this.loading = true;
        try {
            this.data = await api.getData();
        } finally {
            this.loading = false;
        }
    }
}

export const myState = new MyState();
```

## What NOT to Do

- ❌ Don't manually create shadcn components - use CLI
- ❌ Don't use Tailwind v3 syntax (`@tailwind base;`)
- ❌ Don't forget base path in navigation (`{base}/path`)
- ❌ Don't use `any` type - use proper type guards
- ❌ Don't use "enhanced" or "extended" in names
- ❌ Don't bypass the API client for fetch calls
- ❌ Don't disable ESLint rules without justification
- ❌ Don't forget `credentials: 'include'` for authenticated requests
