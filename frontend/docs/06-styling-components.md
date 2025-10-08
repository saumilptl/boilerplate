# Styling & Components

## Tailwind CSS v4

### Setup

Tailwind CSS v4 uses a completely new syntax compared to v3.

**app.css:**

```css
/* Import Tailwind */
@import "tailwindcss";

/* Custom variant for dark mode */
@custom-variant dark (&:is(.dark *));

/* CSS Variables */
:root {
    --radius: 0.5rem;

    /* Colors (must use hsl() wrapper) */
    --background: hsl(0 0% 100%);
    --foreground: hsl(240 10% 10%);
    --primary: hsl(240 5.9% 10%);
    --primary-foreground: hsl(0 0% 100%);
    --muted: hsl(240 4.8% 95.9%);
    --muted-foreground: hsl(240 3.8% 46.1%);
    /* ... more colors */
}

/* CRITICAL: @theme inline directive */
@theme inline {
    --color-background: var(--background);
    --color-foreground: var(--foreground);
    --color-primary: var(--primary);
    --color-primary-foreground: var(--primary-foreground);
    --color-muted: var(--muted);
    --color-muted-foreground: var(--muted-foreground);
    /* ... more theme mappings */

    --radius-sm: calc(var(--radius) - 4px);
    --radius-md: calc(var(--radius) - 2px);
    --radius-lg: var(--radius);
}

/* Base styles */
@layer base {
    * {
        @apply border-border;
    }
    body {
        @apply bg-background text-foreground;
    }
}
```

**vite.config.ts:**

```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';  // v4 Vite plugin

export default defineConfig({
    plugins: [
        tailwindcss(),  // Add before sveltekit
        sveltekit()
    ]
});
```

### Key Differences from v3

| v3 | v4 |
|----|-----|
| `@tailwind base;` | `@import "tailwindcss";` |
| `tailwind.config.js` | `@theme inline { }` in CSS |
| No wrapper needed | `hsl()` wrapper required |
| `@apply` anywhere | `@apply` only in `@layer` |

### Common Classes

```svelte
<!-- Layout -->
<div class="flex items-center justify-between">
<div class="grid gap-4">
<div class="space-y-2">

<!-- Typography -->
<h1 class="text-2xl font-bold">
<p class="text-sm text-muted-foreground">

<!-- Spacing -->
<div class="p-6 m-4">
<div class="px-4 py-2">

<!-- Colors -->
<div class="bg-background text-foreground">
<div class="bg-primary text-primary-foreground">
<div class="bg-muted text-muted-foreground">

<!-- Borders & Radius -->
<div class="border rounded-lg">
<div class="border-border rounded-md">

<!-- States -->
<button class="hover:bg-accent hover:text-accent-foreground">
<input class="focus:ring-2 focus:ring-ring">
```

## shadcn-svelte Components

### Installation

**Initial Setup:**

```bash
npx shadcn-svelte@next init
```

This creates:
- `components.json` - Configuration
- `lib/components/ui/` - Component directory
- Updates `app.css` with CSS variables

**Add Components:**

```bash
# Add individual components
npx shadcn-svelte@next add button
npx shadcn-svelte@next add card
npx shadcn-svelte@next add input
npx shadcn-svelte@next add label
npx shadcn-svelte@next add dialog
npx shadcn-svelte@next add dropdown-menu

# List available components
npx shadcn-svelte@next add
```

### Component Structure

Components use a **compound pattern**:

```svelte
<script lang="ts">
    import * as Card from '$lib/components/ui/card';
</script>

<Card.Root>
    <Card.Header>
        <Card.Title>Card Title</Card.Title>
        <Card.Description>Card description text</Card.Description>
    </Card.Header>
    <Card.Content>
        <!-- Main content -->
    </Card.Content>
    <Card.Footer>
        <!-- Footer content -->
    </Card.Footer>
</Card.Root>
```

### Button

```svelte
<script lang="ts">
    import { Button } from '$lib/components/ui/button';
</script>

<!-- Variants -->
<Button>Default</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="destructive">Destructive</Button>
<Button variant="link">Link</Button>

<!-- Sizes -->
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
<Button size="icon">
    <Icon />
</Button>

<!-- States -->
<Button disabled>Disabled</Button>
<Button onclick={() => console.log('clicked')}>Click me</Button>
```

### Card

```svelte
<script lang="ts">
    import * as Card from '$lib/components/ui/card';
    import { Button } from '$lib/components/ui/button';
</script>

<Card.Root>
    <Card.Header>
        <Card.Title>Create Account</Card.Title>
        <Card.Description>
            Enter your details to create a new account
        </Card.Description>
    </Card.Header>
    <Card.Content class="space-y-4">
        <!-- Form fields -->
    </Card.Content>
    <Card.Footer class="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Submit</Button>
    </Card.Footer>
</Card.Root>
```

### Input & Label

```svelte
<script lang="ts">
    import { Input } from '$lib/components/ui/input';
    import { Label } from '$lib/components/ui/label';

    let email = $state('');
</script>

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
```

### Dialog

```svelte
<script lang="ts">
    import * as Dialog from '$lib/components/ui/dialog';
    import { Button } from '$lib/components/ui/button';

    let open = $state(false);
</script>

<Dialog.Root bind:open>
    <Dialog.Trigger asChild let:builder>
        <Button builders={[builder]}>Open Dialog</Button>
    </Dialog.Trigger>
    <Dialog.Content>
        <Dialog.Header>
            <Dialog.Title>Confirm Action</Dialog.Title>
            <Dialog.Description>
                Are you sure you want to continue?
            </Dialog.Description>
        </Dialog.Header>
        <Dialog.Footer>
            <Button variant="outline" onclick={() => open = false}>
                Cancel
            </Button>
            <Button onclick={() => {
                // Handle confirm
                open = false;
            }}>
                Confirm
            </Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>
```

### Dropdown Menu

```svelte
<script lang="ts">
    import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
    import { Button } from '$lib/components/ui/button';
</script>

<DropdownMenu.Root>
    <DropdownMenu.Trigger asChild let:builder>
        <Button variant="outline" builders={[builder]}>
            Options
        </Button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content>
        <DropdownMenu.Label>My Account</DropdownMenu.Label>
        <DropdownMenu.Separator />
        <DropdownMenu.Item onclick={() => console.log('Profile')}>
            Profile
        </DropdownMenu.Item>
        <DropdownMenu.Item onclick={() => console.log('Settings')}>
            Settings
        </DropdownMenu.Item>
        <DropdownMenu.Separator />
        <DropdownMenu.Item onclick={() => console.log('Logout')}>
            Logout
        </DropdownMenu.Item>
    </DropdownMenu.Content>
</DropdownMenu.Root>
```

## Custom Components

### Creating a Component

```svelte
<!-- lib/components/UserAvatar.svelte -->
<script lang="ts">
    type UserAvatarProps = {
        name: string;
        email?: string;
        size?: 'sm' | 'md' | 'lg';
    };

    let { name, email, size = 'md' }: UserAvatarProps = $props();

    const sizeClasses = {
        sm: 'h-8 w-8 text-xs',
        md: 'h-10 w-10 text-sm',
        lg: 'h-12 w-12 text-base'
    };

    const initials = name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
</script>

<div
    class="flex items-center justify-center rounded-full bg-primary text-primary-foreground {sizeClasses[size]}"
    title={email}
>
    {initials}
</div>
```

### Using Custom Component

```svelte
<script lang="ts">
    import UserAvatar from '$lib/components/UserAvatar.svelte';
</script>

<UserAvatar name="John Doe" email="john@example.com" size="lg" />
```

## Styling Patterns

### Container Layouts

```svelte
<!-- Centered container -->
<div class="container mx-auto max-w-4xl p-6">
    <!-- Content -->
</div>

<!-- Full-height centered -->
<div class="flex min-h-screen items-center justify-center">
    <!-- Centered content -->
</div>

<!-- Grid layout -->
<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
    <!-- Grid items -->
</div>
```

### Forms

```svelte
<form class="space-y-4">
    <div class="grid gap-2">
        <Label for="field">Label</Label>
        <Input id="field" />
    </div>
    <Button type="submit" class="w-full">Submit</Button>
</form>
```

### Loading States

```svelte
{#if loading}
    <div class="flex items-center justify-center p-6">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
{/if}
```

### Error Messages

```svelte
{#if error}
    <div class="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
        {error}
    </div>
{/if}
```

### Responsive Design

```svelte
<!-- Mobile first -->
<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">

<!-- Hide on mobile -->
<div class="hidden md:block">

<!-- Show only on mobile -->
<div class="block md:hidden">

<!-- Responsive text -->
<h1 class="text-2xl md:text-3xl lg:text-4xl">
```

## Dark Mode

### Setup

```typescript
// lib/state/theme.svelte.ts
class ThemeState {
    theme = $state<'light' | 'dark'>('light');

    constructor() {
        // Load from localStorage
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('theme') as 'light' | 'dark' | null;
            this.theme = saved || 'light';
        }

        // Sync to DOM and localStorage
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

### Dark Mode Styles

In `app.css`:

```css
.dark {
    --background: hsl(240 10% 3.9%);
    --foreground: hsl(0 0% 98%);
    --primary: hsl(0 0% 98%);
    --primary-foreground: hsl(240 5.9% 10%);
    /* ... more dark colors */
}
```

### Theme Toggle

```svelte
<script lang="ts">
    import { Button } from '$lib/components/ui/button';
    import { themeState } from '$lib/state/theme.svelte';
</script>

<Button variant="ghost" size="icon" onclick={() => themeState.toggle()}>
    {#if themeState.theme === 'light'}
        🌙
    {:else}
        ☀️
    {/if}
</Button>
```

## Common Issues

### Styles Not Applying

1. Check `@import "tailwindcss";` (not `@tailwind base;`)
2. Verify `@theme inline` directive exists
3. Ensure CSS variables use `hsl()` wrapper
4. Check Tailwind plugin in vite.config.ts

### Component Not Found

```bash
# Install the component
npx shadcn-svelte@next add <component-name>
```

### Wrong Component Behavior

- Verify using compound pattern (Card.Root, not <Card>)
- Check props are being passed correctly
- Review component documentation

## Best Practices

1. **Use shadcn components** - Don't reinvent the wheel
2. **Follow Tailwind utilities** - Avoid custom CSS when possible
3. **Keep components small** - Single responsibility
4. **Use semantic HTML** - Accessibility matters
5. **Responsive by default** - Mobile-first approach
6. **Consistent spacing** - Use Tailwind's spacing scale
7. **Color system** - Use CSS variables, not hardcoded colors

## What NOT to Do

- ❌ Don't manually create shadcn components
- ❌ Don't use Tailwind v3 syntax
- ❌ Don't forget `hsl()` wrapper in CSS variables
- ❌ Don't use inline styles when Tailwind utilities exist
- ❌ Don't hardcode colors - use theme variables
- ❌ Don't nest `@apply` outside of `@layer`
