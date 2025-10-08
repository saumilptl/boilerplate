import type { LayoutLoad } from './$types';
import { browser } from '$app/environment';
import { authState } from '$lib/state/auth.svelte';

export const ssr = false; // Disable SSR for auth handling

export const load: LayoutLoad = async () => {
	// Always try to fetch user on initial load in browser
	if (browser) {
		try {
			await authState.fetchUser();
		} catch {
			// User not authenticated - this is expected for logged out users
		}
	}

	return {};
};
