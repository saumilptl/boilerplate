import { goto } from '$app/navigation';
import { base } from '$app/paths';
import { API_BASE_URL, ENDPOINTS } from '$lib/api/config';
import * as authApi from '$lib/api/auth';
import { LoginRequestSchema, type AuthUser } from '$lib/schemas/auth';

class AuthState {
	user = $state<AuthUser | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	// Derived state
	isAuthenticated = $derived(this.user !== null);

	async login(email: string, password: string) {
		this.loading = true;
		this.error = null;

		try {
			// Validate input
			const credentials = LoginRequestSchema.parse({
				username: email,
				password
			});

			const formData = new URLSearchParams();
			formData.append('username', credentials.username);
			formData.append('password', credentials.password);

			const loginUrl = `${API_BASE_URL}${ENDPOINTS.AUTH.LOGIN}`;

			const response = await fetch(loginUrl, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded'
				},
				body: formData,
				credentials: 'include'
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
				const errorMessage = errorData.detail || 'Login failed';
				throw new Error(errorMessage);
			}

			// Fetch user data after successful login
			await this.fetchUser();

			// Redirect to home page
			await goto(`${base}/home`);

			return true;
		} catch (error) {
			if (error && typeof error === 'object' && 'issues' in error && Array.isArray(error.issues)) {
				// Zod validation error
				this.error = error.issues[0]?.message || 'Invalid input';
			} else if (error instanceof Error) {
				this.error = error.message || 'Login failed';
			} else {
				this.error = 'Login failed';
			}
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

	async register(full_name: string, email: string, password: string) {
		this.loading = true;
		this.error = null;

		try {
			await authApi.register({
				full_name,
				email,
				password
			});

			// After successful registration, redirect to login
			await goto(`${base}/login`);

			return true;
		} catch (error) {
			if (error && typeof error === 'object' && 'issues' in error && Array.isArray(error.issues)) {
				// Zod validation error
				this.error = error.issues[0]?.message || 'Invalid input';
			} else if (error instanceof Error) {
				this.error = error.message || 'Registration failed';
			} else {
				this.error = 'Registration failed';
			}
			throw error;
		} finally {
			this.loading = false;
		}
	}

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

	async initialize() {
		await this.fetchUser();
	}
}

export const authState = new AuthState();
