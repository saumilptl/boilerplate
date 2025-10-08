<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import * as Card from '$lib/components/ui/card';
	import { authState } from '$lib/state/auth.svelte';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	let email = $state('');
	let password = $state('');

	// Redirect if already authenticated
	$effect(() => {
		if (browser && authState.isAuthenticated) {
			goto(`${base}/home`);
		}
	});

	async function handleLogin() {
		try {
			await authState.login(email, password);
		} catch (err) {
			// Error is already set in authState
			console.error('Login error:', err);
		}
	}
</script>

<svelte:head>
	<title>Login</title>
</svelte:head>

<div class="bg-muted flex min-h-svh items-center justify-center p-6 md:p-10">
	<div class="w-full max-w-sm">
		<Card.Root>
			<Card.Header>
				<Card.Title class="text-2xl">Welcome back</Card.Title>
				<Card.Description>
					Enter your email and password to sign in to your account
				</Card.Description>
			</Card.Header>
			<Card.Content>
				<form on:submit|preventDefault={handleLogin} class="grid gap-4">
					<div class="grid gap-2">
						<Label for="email">Email</Label>
						<Input
							id="email"
							type="email"
							placeholder="m@example.com"
							bind:value={email}
							required
							disabled={authState.loading}
						/>
					</div>

					<div class="grid gap-2">
						<Label for="password">Password</Label>
						<Input
							id="password"
							type="password"
							placeholder="••••••••"
							bind:value={password}
							required
							disabled={authState.loading}
						/>
					</div>

					{#if authState.error}
						<div class="bg-destructive/10 text-destructive rounded-lg p-3 text-sm">
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
