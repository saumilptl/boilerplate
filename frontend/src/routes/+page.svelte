<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { authState } from '$lib/state/auth.svelte';
	import { onMount } from 'svelte';

	onMount(() => {
		// Redirect based on auth state
		if (authState.isAuthenticated) {
			goto(`${base}/home`);
		} else {
			goto(`${base}/login`);
		}
	});
</script>

<div class="flex min-h-screen items-center justify-center">
	<div class="border-primary h-8 w-8 animate-spin rounded-full border-b-2"></div>
</div>
// test comment
