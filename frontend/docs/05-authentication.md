# Authentication

## Overview

Authentication uses **cookie-based JWT** with the backend's FastAPI Users implementation.

- JWT tokens stored in HttpOnly cookies
- Automatic cookie sending with `credentials: 'include'`
- Protected routes with auth guards
- Persistent sessions across page reloads

## Authentication Flow

### 1. Login

```typescript
// lib/state/auth.svelte.ts
async login(email: string, password: string) {
    this.loading = true;
    this.error = null;

    try {
        // Validate input
        const credentials = LoginRequestSchema.parse({
            username: email,
            password
        });

        // Create form data (login uses application/x-www-form-urlencoded)
        const formData = new URLSearchParams();
        formData.append('username', credentials.username);
        formData.append('password', credentials.password);

        // Send login request
        const response = await fetch(`${API_BASE_URL}${ENDPOINTS.AUTH.LOGIN}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData,
            credentials: 'include'  // Important: sends and receives cookies
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        // Cookie is set by backend automatically
        // Now fetch user data
        await this.fetchUser();

        // Redirect to home
        await goto(`${base}/home`);

        return true;
    } catch (error) {
        this.error = error instanceof Error ? error.message : 'Login failed';
        throw error;
    } finally {
        this.loading = false;
    }
}
```

### 2. Fetch Current User

```typescript
async fetchUser() {
    this.loading = true;
    try {
        const user = await authApi.getCurrentUser();
        this.user = user;
        return user;
    } catch {
        this.user = null;
        return null;
    } finally {
        this.loading = false;
    }
}
```

### 3. Logout

```typescript
async logout() {
    this.loading = true;
    try {
        await authApi.logout();
        this.user = null;
        await goto(`${base}/login`);
    } catch (error) {
        this.error = error instanceof Error ? error.message : 'Logout failed';
        throw error;
    } finally {
        this.loading = false;
    }
}
```

## API Integration

### Auth Service

```typescript
// lib/api/auth.ts
import { api } from './client';
import { ENDPOINTS } from './config';
import { AuthUserSchema } from '$lib/schemas/auth';
import type { RegisterRequest } from '$lib/schemas/auth';

export async function getCurrentUser(): Promise<AuthUser | null> {
    try {
        const response = await api.get(ENDPOINTS.AUTH.ME);
        return AuthUserSchema.parse(response);
    } catch (error) {
        if (error && typeof error === 'object' && 'status' in error && error.status === 401) {
            return null;
        }
        throw error;
    }
}

export async function register(data: RegisterRequest): Promise<void> {
    const validatedData = RegisterRequestSchema.parse(data);
    await api.post(ENDPOINTS.AUTH.REGISTER, validatedData);
}

export async function logout(): Promise<void> {
    await api.post(ENDPOINTS.AUTH.LOGOUT);
}
```

### API Endpoints Configuration

```typescript
// lib/api/config.ts
import { PUBLIC_API_URL } from '$env/static/public';
import { base } from '$app/paths';

export const API_BASE_URL = PUBLIC_API_URL || `${base}/api`;

export const ENDPOINTS = {
    AUTH: {
        LOGIN: '/auth/cookie/login',      // Cookie-based login
        LOGOUT: '/auth/cookie/logout',    // Cookie-based logout
        ME: '/auth/users/me',             // Get current user
        REGISTER: '/auth/register'        // User registration
    }
} as const;
```

## Schemas

```typescript
// lib/schemas/auth.ts
import { z } from 'zod';

export const LoginRequestSchema = z.object({
    username: z.string().email('Please enter a valid email'),
    password: z.string().min(1, 'Password is required')
});

export const RegisterRequestSchema = z.object({
    email: z.string().email('Please enter a valid email'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    full_name: z.string().min(1, 'Full name is required')
});

export const AuthUserSchema = z.object({
    id: z.string(),
    email: z.string().email(),
    full_name: z.string().optional(),
    is_active: z.boolean(),
    is_verified: z.boolean()
});

export type LoginRequest = z.infer<typeof LoginRequestSchema>;
export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type AuthUser = z.infer<typeof AuthUserSchema>;
```

## Route Protection

### Protected Routes

```
routes/
├── (protected)/
│   ├── +layout.svelte    # Auth guard
│   └── home/
│       └── +page.svelte
```

**Auth Guard** (`(protected)/+layout.svelte`):

```svelte
<script lang="ts">
    import { authState } from '$lib/state/auth.svelte';
    import { goto } from '$app/navigation';
    import { base } from '$app/paths';
    import { browser } from '$app/environment';
    import { page } from '$app/stores';

    let { children } = $props();

    // Client-side auth check
    $effect(() => {
        if (browser && !authState.loading && !authState.isAuthenticated) {
            // Redirect to login with return URL
            const redirectTo = encodeURIComponent($page.url.pathname + $page.url.search);
            goto(`${base}/login?redirectTo=${redirectTo}`);
        }
    });
</script>

{#if authState.isAuthenticated}
    {@render children?.()}
{:else if authState.loading}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p class="mt-2 text-sm text-muted-foreground">Loading...</p>
        </div>
    </div>
{/if}
```

### Public Routes

```
routes/
├── (public)/
│   ├── login/
│   │   └── +page.svelte
│   └── signup/
│       └── +page.svelte
```

**Login Page with Redirect** (`(public)/login/+page.svelte`):

```svelte
<script lang="ts">
    import { authState } from '$lib/state/auth.svelte';
    import { base } from '$app/paths';
    import { goto } from '$app/navigation';
    import { browser } from '$app/environment';
    import { page } from '$app/stores';

    let email = $state('');
    let password = $state('');

    // Redirect if already authenticated
    $effect(() => {
        if (browser && authState.isAuthenticated) {
            // Check for return URL
            const redirectTo = $page.url.searchParams.get('redirectTo');
            goto(redirectTo || `${base}/home`);
        }
    });

    async function handleLogin() {
        try {
            await authState.login(email, password);
            // authState.login handles redirect
        } catch (err) {
            console.error('Login error:', err);
        }
    }
</script>

<!-- Login form -->
```

## Session Persistence

### Initialize on App Load

```typescript
// routes/+layout.ts
import type { LayoutLoad } from './$types';
import { browser } from '$app/environment';
import { authState } from '$lib/state/auth.svelte';

export const ssr = false; // Disable SSR for client-side auth

export const load: LayoutLoad = async () => {
    if (browser) {
        try {
            // Attempt to restore session from cookie
            await authState.fetchUser();
        } catch {
            // User not authenticated - this is expected
        }
    }
    return {};
};
```

### Root Layout

```svelte
<!-- routes/+layout.svelte -->
<script lang="ts">
    import '../app.css';
    let { children } = $props();
</script>

<main class="min-h-screen">
    {@render children?.()}
</main>
```

## Backend Configuration

### Cookie Settings

Backend must configure cookies properly for browser auth:

```python
# backend/app/auth/dependencies.py
from fastapi_users.authentication import CookieTransport

cookie_transport = CookieTransport(
    cookie_name="auth-token",
    cookie_max_age=3600,  # 1 hour
    cookie_secure=True,   # Required for HTTPS
    cookie_httponly=True, # Prevents XSS
    cookie_samesite="none"  # Required for cross-site cookies (ngrok)
)
```

### CORS Configuration

```python
# backend/secrets/development.json
{
    "SECURITY": {
        "CORS_ORIGINS": [
            "http://localhost:5173",
            "http://localhost:8080",
            "https://your-domain.ngrok.app"
        ],
        "CORS_ALLOW_CREDENTIALS": true
    }
}
```

## UI Components

### Login Form

```svelte
<script lang="ts">
    import { Button } from '$lib/components/ui/button';
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';
    import * as Card from '$lib/components/ui/card';
    import { authState } from '$lib/state/auth.svelte';
    import { base } from '$app/paths';

    let email = $state('');
    let password = $state('');

    async function handleLogin() {
        try {
            await authState.login(email, password);
        } catch (err) {
            console.error('Login error:', err);
        }
    }
</script>

<div class="flex min-h-svh items-center justify-center bg-muted p-6">
    <div class="w-full max-w-sm">
        <Card.Root>
            <Card.Header>
                <Card.Title class="text-2xl">Welcome back</Card.Title>
                <Card.Description>
                    Enter your email and password to sign in
                </Card.Description>
            </Card.Header>
            <Card.Content>
                <form on:submit|preventDefault={handleLogin} class="grid gap-4">
                    <div class="grid gap-2">
                        <Label for="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="you@example.com"
                            bind:value={email}
                            required
                        />
                    </div>
                    <div class="grid gap-2">
                        <Label for="password">Password</Label>
                        <Input
                            id="password"
                            type="password"
                            bind:value={password}
                            required
                        />
                    </div>
                    {#if authState.error}
                        <div class="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                            {authState.error}
                        </div>
                    {/if}
                    <Button type="submit" class="w-full" disabled={authState.loading}>
                        {authState.loading ? 'Signing in...' : 'Sign in'}
                    </Button>
                </form>
            </Card.Content>
            <Card.Footer>
                <div class="text-muted-foreground text-center text-sm">
                    Don't have an account?
                    <a href="{base}/signup" class="hover:text-primary underline underline-offset-4">
                        Sign up
                    </a>
                </div>
            </Card.Footer>
        </Card.Root>
    </div>
</div>
```

### Protected Page

```svelte
<script lang="ts">
    import { authState } from '$lib/state/auth.svelte';
    import { Button } from '$lib/components/ui/button';
    import * as Card from '$lib/components/ui/card';

    async function handleLogout() {
        try {
            await authState.logout();
        } catch (err) {
            console.error('Logout error:', err);
        }
    }
</script>

<div class="flex min-h-screen items-center justify-center bg-muted p-6">
    <Card.Root>
        <Card.Header>
            <Card.Title>Welcome!</Card.Title>
            <Card.Description>You are logged in</Card.Description>
        </Card.Header>
        <Card.Content>
            <div class="space-y-2">
                <div class="flex justify-between">
                    <span class="text-sm font-medium">Email:</span>
                    <span class="text-sm">{authState.user?.email}</span>
                </div>
                {#if authState.user?.full_name}
                    <div class="flex justify-between">
                        <span class="text-sm font-medium">Name:</span>
                        <span class="text-sm">{authState.user.full_name}</span>
                    </div>
                {/if}
            </div>
        </Card.Content>
        <Card.Footer>
            <Button variant="outline" class="w-full" onclick={handleLogout}>
                Sign out
            </Button>
        </Card.Footer>
    </Card.Root>
</div>
```

## Debugging

### Check Cookie

Browser DevTools → Application → Cookies → Check for `auth-token`

### Network Tab

Look for:
- Login request sends credentials
- Subsequent requests include cookie automatically
- 401 responses redirect to login

### Console Logging

```typescript
$effect(() => {
    console.log('Auth state:', {
        user: authState.user,
        loading: authState.loading,
        isAuthenticated: authState.isAuthenticated
    });
});
```

## Common Issues

### Cookie Not Being Set

- Check backend `cookie_secure` setting matches protocol (HTTP vs HTTPS)
- Verify `cookie_samesite` is "none" for cross-origin (ngrok)
- Check CORS settings allow credentials

### 401 Errors on Protected Routes

- Verify `credentials: 'include'` in all API calls
- Check cookie is being sent in request headers
- Verify token hasn't expired

### Infinite Redirect Loop

- Check auth guard isn't protecting login page
- Verify `(public)` routes don't have auth guard
- Check redirect logic in `$effect`

## Best Practices

1. **Always use `credentials: 'include'`** in fetch calls
2. **Initialize auth on app load** in root layout
3. **Handle loading states** during auth checks
4. **Use route groups** for protected/public routes
5. **Validate input** with Zod before sending
6. **Display user-friendly errors** in UI
7. **Redirect with return URL** for better UX
8. **Check `browser` flag** before auth operations
