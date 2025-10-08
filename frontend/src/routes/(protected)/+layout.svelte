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
			// Preserve the current URL for redirect after login
			const redirectTo = encodeURIComponent($page.url.pathname + $page.url.search);
			goto(`${base}/login?redirectTo=${redirectTo}`);
		}
	});
</script>

{#if authState.isAuthenticated}
	{@render children()}
{:else if authState.loading}
	<div class="flex min-h-screen items-center justify-center">
		<div class="text-center">
			<div class="border-primary mx-auto h-8 w-8 animate-spin rounded-full border-b-2"></div>
			<p class="text-muted-foreground mt-2 text-sm">Loading...</p>
		</div>
	</div>
{/if}
