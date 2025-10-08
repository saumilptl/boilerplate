import * as api from './client';
import { ENDPOINTS } from './config';
import {
	AuthUserSchema,
	LoginRequestSchema,
	RegisterRequestSchema,
	type AuthUser,
	type LoginRequest,
	type RegisterRequest
} from '$lib/schemas/auth';

/**
 * Login with email and password
 * @param credentials - Email (as username) and password
 * @returns Promise<void> - Sets cookie on success
 */
export async function login(credentials: LoginRequest): Promise<void> {
	// Validate request
	const validatedCredentials = LoginRequestSchema.parse(credentials);

	const formData = new URLSearchParams();
	formData.append('username', validatedCredentials.username);
	formData.append('password', validatedCredentials.password);

	await api.post(ENDPOINTS.AUTH.LOGIN, formData, {
		headers: {
			'Content-Type': 'application/x-www-form-urlencoded'
		}
	});
}

/**
 * Get current user
 * @returns Promise<AuthUser | null>
 */
export async function getCurrentUser(): Promise<AuthUser | null> {
	try {
		const response = await api.get(ENDPOINTS.AUTH.ME);
		return AuthUserSchema.parse(response);
	} catch (error) {
		if (error && typeof error === 'object' && 'status' in error && error.status === 401) {
			return null;
		}
		throw error;
	}
}

/**
 * Register a new user
 * @param data - Registration data (email, password, full_name)
 * @returns Promise<void>
 */
export async function register(data: RegisterRequest): Promise<void> {
	// Validate request
	const validatedData = RegisterRequestSchema.parse(data);

	await api.post(ENDPOINTS.AUTH.REGISTER, validatedData);
}

/**
 * Logout current user
 * @returns Promise<void>
 */
export async function logout(): Promise<void> {
	await api.post(ENDPOINTS.AUTH.LOGOUT);
}
