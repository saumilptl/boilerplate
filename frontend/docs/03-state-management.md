# State Management

## Overview

State management uses **Svelte 5 runes** with a singleton class pattern for global stores.

## Svelte 5 Runes

### Core Runes

```typescript
// $state - Reactive state
let count = $state(0);
let user = $state<User | null>(null);

// $derived - Computed values
let doubled = $derived(count * 2);
let isLoggedIn = $derived(user !== null);

// $effect - Side effects
$effect(() => {
    console.log('Count changed:', count);
});
```

### Runes in Classes

```typescript
class CounterState {
    count = $state(0);
    doubled = $derived(this.count * 2);

    increment() {
        this.count += 1;
    }
}

export const counter = new CounterState();
```

## State Store Pattern

### Creating a Store

```typescript
// lib/state/auth.svelte.ts
import type { AuthUser } from '$lib/schemas/auth';

class AuthState {
    // Reactive state
    user = $state<AuthUser | null>(null);
    loading = $state(false);
    error = $state<string | null>(null);

    // Derived state
    isAuthenticated = $derived(this.user !== null);

    // Methods
    async login(email: string, password: string) {
        this.loading = true;
        this.error = null;

        try {
            // Login logic
            await authApi.login(email, password);
            await this.fetchUser();
        } catch (error) {
            this.error = 'Login failed';
            throw error;
        } finally {
            this.loading = false;
        }
    }

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

    async logout() {
        this.loading = true;
        try {
            await authApi.logout();
            this.user = null;
        } finally {
            this.loading = false;
        }
    }
}

export const authState = new AuthState();
```

### Using a Store

```svelte
<script lang="ts">
    import { authState } from '$lib/state/auth.svelte';

    // Access reactive state
    const user = authState.user;
    const loading = authState.loading;
    const isAuthenticated = authState.isAuthenticated;

    // Call methods
    async function handleLogin() {
        await authState.login(email, password);
    }
</script>

{#if loading}
    <p>Loading...</p>
{:else if isAuthenticated}
    <p>Welcome, {user?.email}</p>
    <button onclick={() => authState.logout()}>Logout</button>
{:else}
    <button onclick={handleLogin}>Login</button>
{/if}
```

## Store Guidelines

### 1. File Naming

```
lib/state/
├── auth.svelte.ts       # Auth state
├── posts.svelte.ts      # Posts state
└── ui.svelte.ts         # UI state (modals, toasts, etc.)
```

Must use `.svelte.ts` extension for files containing runes.

### 2. Keep Stores Focused

```typescript
// ✅ Good - Single responsibility
class AuthState {
    user = $state<User | null>(null);
    // ... auth-related state only
}

class PostsState {
    posts = $state<Post[]>([]);
    // ... posts-related state only
}

// ❌ Bad - Too much responsibility
class AppState {
    user = $state<User | null>(null);
    posts = $state<Post[]>([]);
    comments = $state<Comment[]>([]);
    // ... too many concerns
}
```

### 3. Use Derived State

```typescript
class PostsState {
    posts = $state<Post[]>([]);
    filter = $state<'all' | 'published'>('all');

    // ✅ Good - Derived from reactive state
    filteredPosts = $derived(
        this.filter === 'all'
            ? this.posts
            : this.posts.filter(p => p.published)
    );

    // ❌ Bad - Manual computed state
    getFilteredPosts() {
        return this.filter === 'all'
            ? this.posts
            : this.posts.filter(p => p.published);
    }
}
```

### 4. Handle Loading and Errors

```typescript
class DataState {
    data = $state<Data[]>([]);
    loading = $state(false);
    error = $state<string | null>(null);

    async fetch() {
        this.loading = true;
        this.error = null;

        try {
            this.data = await api.getData();
        } catch (error) {
            if (error instanceof Error) {
                this.error = error.message;
            } else {
                this.error = 'Failed to fetch data';
            }
            throw error;
        } finally {
            this.loading = false;
        }
    }
}
```

## Side Effects

### Using $effect

```typescript
class ThemeState {
    theme = $state<'light' | 'dark'>('light');

    constructor() {
        // Load theme from localStorage
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('theme');
            if (saved === 'light' || saved === 'dark') {
                this.theme = saved;
            }
        }

        // Sync to localStorage when changed
        $effect(() => {
            if (typeof window !== 'undefined') {
                localStorage.setItem('theme', this.theme);
                document.documentElement.classList.toggle('dark', this.theme === 'dark');
            }
        });
    }

    toggle() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
    }
}

export const themeState = new ThemeState();
```

### Cleanup in $effect

```typescript
$effect(() => {
    const interval = setInterval(() => {
        // Do something periodically
    }, 1000);

    // Cleanup function
    return () => {
        clearInterval(interval);
    };
});
```

## Local Component State

For component-specific state, use runes directly:

```svelte
<script lang="ts">
    // Component-only state
    let email = $state('');
    let password = $state('');
    let showPassword = $state(false);

    // Computed
    let isValid = $derived(
        email.length > 0 && password.length >= 8
    );

    // Side effect
    $effect(() => {
        console.log('Email changed:', email);
    });
</script>

<input bind:value={email} />
<input type={showPassword ? 'text' : 'password'} bind:value={password} />
<button disabled={!isValid}>Submit</button>
```

## State Initialization

### On App Load

```typescript
// routes/+layout.ts
import type { LayoutLoad } from './$types';
import { browser } from '$app/environment';
import { authState } from '$lib/state/auth.svelte';

export const ssr = false; // Disable SSR for auth

export const load: LayoutLoad = async () => {
    if (browser) {
        try {
            // Initialize auth state
            await authState.fetchUser();
        } catch {
            // User not authenticated - expected
        }
    }
    return {};
};
```

### On Component Mount

```svelte
<script lang="ts">
    import { onMount } from 'svelte';
    import { postsState } from '$lib/state/posts.svelte';

    onMount(() => {
        postsState.fetchPosts();
    });
</script>
```

## Common Patterns

### Optimistic Updates

```typescript
class TodosState {
    todos = $state<Todo[]>([]);

    async addTodo(text: string) {
        // Optimistic update
        const tempId = crypto.randomUUID();
        const tempTodo = { id: tempId, text, completed: false };
        this.todos = [...this.todos, tempTodo];

        try {
            // Make API call
            const created = await api.createTodo({ text });

            // Replace temp with real data
            this.todos = this.todos.map(t =>
                t.id === tempId ? created : t
            );
        } catch (error) {
            // Rollback on error
            this.todos = this.todos.filter(t => t.id !== tempId);
            throw error;
        }
    }
}
```

### Pagination

```typescript
class PostsState {
    posts = $state<Post[]>([]);
    page = $state(1);
    hasMore = $state(true);
    loading = $state(false);

    async loadMore() {
        if (this.loading || !this.hasMore) return;

        this.loading = true;
        try {
            const newPosts = await api.getPosts(this.page + 1);

            if (newPosts.length === 0) {
                this.hasMore = false;
            } else {
                this.posts = [...this.posts, ...newPosts];
                this.page += 1;
            }
        } finally {
            this.loading = false;
        }
    }
}
```

### Debounced Search

```typescript
class SearchState {
    query = $state('');
    results = $state<Result[]>([]);
    loading = $state(false);

    private searchTimeout: ReturnType<typeof setTimeout> | null = null;

    setQuery(value: string) {
        this.query = value;

        // Clear existing timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.search();
        }, 300);
    }

    private async search() {
        if (!this.query) {
            this.results = [];
            return;
        }

        this.loading = true;
        try {
            this.results = await api.search(this.query);
        } finally {
            this.loading = false;
        }
    }
}
```

## Testing State

```typescript
import { describe, it, expect, vi } from 'vitest';
import { AuthState } from '$lib/state/auth.svelte';

describe('AuthState', () => {
    it('should initialize with null user', () => {
        const state = new AuthState();
        expect(state.user).toBeNull();
        expect(state.isAuthenticated).toBe(false);
    });

    it('should set user on successful login', async () => {
        const state = new AuthState();

        // Mock API
        vi.spyOn(authApi, 'login').mockResolvedValue(undefined);
        vi.spyOn(authApi, 'getCurrentUser').mockResolvedValue({
            id: '123',
            email: 'test@example.com'
        });

        await state.login('test@example.com', 'password');

        expect(state.user).not.toBeNull();
        expect(state.isAuthenticated).toBe(true);
    });
});
```

## Best Practices

1. **Single Source of Truth** - Don't duplicate state
2. **Keep Stores Focused** - One concern per store
3. **Use Derived State** - Don't compute in templates
4. **Handle Errors** - Always set error state on failures
5. **Initialize Properly** - Load state in layouts or onMount
6. **Type Safety** - Use TypeScript for all state
7. **Cleanup Effects** - Return cleanup functions from $effect

## What NOT to Do

- ❌ Don't use Svelte 4 stores (`writable`, `readable`)
- ❌ Don't mutate state directly in templates
- ❌ Don't create multiple instances of singleton stores
- ❌ Don't forget `.svelte.ts` extension for files with runes
- ❌ Don't use `$effect` for computed values (use `$derived`)
- ❌ Don't forget to handle loading and error states
