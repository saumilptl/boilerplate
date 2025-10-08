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

<svelte:head>
	<title>Home</title>
</svelte:head>

<div class="bg-muted flex min-h-screen items-center justify-center p-6">
	<div class="w-full max-w-md">
		<Card.Root>
			<Card.Header>
				<Card.Title class="text-2xl">Welcome!</Card.Title>
				<Card.Description>You are successfully logged in</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<span class="text-muted-foreground text-sm font-medium">Email:</span>
						<span class="font-mono text-sm">{authState.user?.email}</span>
					</div>
					{#if authState.user?.full_name}
						<div class="flex items-center justify-between">
							<span class="text-muted-foreground text-sm font-medium">Name:</span>
							<span class="text-sm">{authState.user.full_name}</span>
						</div>
					{/if}
					<div class="flex items-center justify-between">
						<span class="text-muted-foreground text-sm font-medium">Status:</span>
						<span class="text-sm">
							{authState.user?.is_verified ? '✓ Verified' : '✗ Not Verified'}
						</span>
					</div>
				</div>
			</Card.Content>
			<Card.Footer>
				<Button variant="outline" class="w-full" onclick={handleLogout}>Sign out</Button>
			</Card.Footer>
		</Card.Root>
	</div>
</div>
