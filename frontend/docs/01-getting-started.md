# Getting Started

## Prerequisites

- Node.js 20+
- npm 10+
- Backend API running (see backend docs)

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.development`:

```bash
# Optional: Override API URL
# If not set, defaults to /api (relative path through Caddy)
PUBLIC_API_URL=http://localhost:8000/api
```

### 3. Initialize shadcn-svelte (if starting fresh)

```bash
# Initialize shadcn-svelte configuration
npx shadcn-svelte@next init

# Add components as needed
npx shadcn-svelte@next add button
npx shadcn-svelte@next add card
npx shadcn-svelte@next add input
npx shadcn-svelte@next add label
```

### 4. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173/app`

## Verify Installation

### Check Frontend Health

Open browser to `http://localhost:5173/app/login`

You should see the login page with proper styling.

### Test Authentication

1. Create a user via backend:

   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H 'Content-Type: application/json' \
     -d '{
       "email": "test@example.com",
       "password": "SecurePassword123!",
       "full_name": "Test User"
     }'
   ```

2. Login through the UI at `/app/login`

3. You should be redirected to `/app/home`

## Project Structure

```
frontend/
├── src/
│   ├── app.css              # Global styles with Tailwind
│   ├── app.html             # HTML template
│   ├── lib/
│   │   ├── api/            # API client and services
│   │   │   ├── client.ts       # Generic HTTP client
│   │   │   ├── config.ts       # API configuration
│   │   │   └── auth.ts         # Auth service
│   │   ├── components/     # UI components
│   │   │   └── ui/            # shadcn-svelte components
│   │   ├── schemas/        # Zod validation schemas
│   │   │   └── auth.ts
│   │   └── state/          # Global state stores
│   │       └── auth.svelte.ts  # Auth state
│   └── routes/             # File-based routing
│       ├── +layout.ts          # Root layout with auth init
│       ├── +layout.svelte      # Root layout component
│       ├── +page.svelte        # Root redirect page
│       ├── (protected)/        # Auth-required routes
│       │   ├── +layout.svelte  # Auth guard
│       │   └── home/
│       │       └── +page.svelte
│       └── (public)/           # Public routes
│           ├── login/
│           │   └── +page.svelte
│           └── signup/
│               └── +page.svelte
├── static/                 # Static assets
├── svelte.config.js        # SvelteKit configuration
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind configuration
├── tsconfig.json           # TypeScript configuration
└── package.json            # Dependencies and scripts
```

## Configuration Files

### svelte.config.js

```javascript
import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter(),
		paths: {
			base: '/app' // Important: base path for routing
		}
	}
};
```

### vite.config.ts

```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [
		tailwindcss(), // Tailwind v4 Vite plugin
		sveltekit()
	],
	server: {
		host: '0.0.0.0',
		port: 5173
	}
});
```

### app.css (Tailwind v4 syntax)

```css
@import 'tailwindcss';

@custom-variant dark (&:is(.dark *));

:root {
	--radius: 0.5rem;
	--background: hsl(0 0% 100%);
	--foreground: hsl(240 10% 10%);
	/* ... more CSS variables ... */
}

@theme inline {
	--color-background: var(--background);
	--color-foreground: var(--foreground);
	/* ... more theme mappings ... */
}

@layer base {
	* {
		@apply border-border;
	}
	body {
		@apply bg-background text-foreground;
	}
}
```

## Common Issues

### Tailwind Styles Not Working

**Symptoms**: Components render but have no styling

**Solution**:

1. Verify `@import "tailwindcss";` in app.css (NOT `@tailwind base;`)
2. Check `@theme inline` directive exists
3. Ensure `@tailwindcss/vite` plugin in vite.config.ts
4. Verify CSS variables wrapped with `hsl()`:
   ```css
   --background: hsl(0 0% 100%); /* ✅ Correct */
   --background: 0 0% 100%; /* ❌ Wrong */
   ```

### 404 on Routes

**Symptoms**: Routes don't work, getting 404 errors

**Solution**:

1. Check base path is set in svelte.config.js
2. Verify all navigation uses `{base}` or `${base}`:
   ```svelte
   <a href="{base}/login">Login</a>
   ```
   ```typescript
   await goto(`${base}/home`);
   ```

### Auth Cookie Not Being Sent

**Symptoms**: 401 errors on protected endpoints

**Solution**:

1. Verify `credentials: 'include'` in fetch calls
2. Check backend CORS settings allow credentials
3. Ensure backend sets cookie with `SameSite=none` and `Secure=true`

### Module Not Found Errors

**Symptoms**: Import errors for components

**Solution**:

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- Read [Routing & Navigation](./02-routing-navigation.md) to understand SvelteKit routing
- Review [State Management](./03-state-management.md) for Svelte 5 runes
- See [Authentication](./05-authentication.md) for auth flow details
