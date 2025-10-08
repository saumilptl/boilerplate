<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import * as Card from '$lib/components/ui/card';
	import { authState } from '$lib/state/auth.svelte';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	let full_name = $state('');
	let email = $state('');
	let password = $state('');

	// Redirect if already authenticated
	$effect(() => {
		if (browser && authState.isAuthenticated) {
			goto(`${base}/home`);
		}
	});

	async function handleSignup() {
		try {
			await authState.register(full_name, email, password);
		} catch (err) {
			// Error is already set in authState
			console.error('Signup error:', err);
		}
	}
</script>

<svelte:head>
	<title>Sign Up</title>
</svelte:head>

<div class="bg-muted flex min-h-svh items-center justify-center p-6 md:p-10">
	<div class="w-full max-w-sm">
		<Card.Root>
			<Card.Header>
				<Card.Title class="text-2xl">Create an account</Card.Title>
				<Card.Description>Enter your information to create your account</Card.Description>
			</Card.Header>
			<Card.Content>
				<form on:submit|preventDefault={handleSignup} class="grid gap-4">
					<div class="grid gap-2">
						<Label for="full_name">Full Name</Label>
						<Input
							id="full_name"
							type="text"
							placeholder="John Doe"
							bind:value={full_name}
							required
							disabled={authState.loading}
						/>
					</div>

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
						<p class="text-muted-foreground text-xs">Must be at least 8 characters</p>
					</div>

					{#if authState.error}
						<div class="bg-destructive/10 text-destructive rounded-lg p-3 text-sm">
							{authState.error}
						</div>
					{/if}

					<Button type="submit" class="w-full" disabled={authState.loading}>
						{authState.loading ? 'Creating account...' : 'Create account'}
					</Button>
				</form>
			</Card.Content>
			<Card.Footer>
				<div class="text-muted-foreground text-center text-sm">
					Already have an account?
					<a href="{base}/login" class="hover:text-primary underline underline-offset-4">
						Sign in
					</a>
				</div>
			</Card.Footer>
		</Card.Root>
	</div>
</div>
