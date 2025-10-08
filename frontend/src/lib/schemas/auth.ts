import { z } from 'zod';
import type { components } from '$lib/api/generated/schema';

/**
 * OpenAPI-generated types for runtime validation alignment
 */
type UserReadFromAPI = components['schemas']['UserRead'];

/**
 * Login request schema
 */
export const LoginRequestSchema = z.object({
	username: z.string().email('Please enter a valid email'),
	password: z.string().min(1, 'Password is required')
});

export type LoginRequest = z.infer<typeof LoginRequestSchema>;

/**
 * Register request schema
 * Matches OpenAPI UserCreate schema
 */
export const RegisterRequestSchema = z.object({
	email: z.string().email('Please enter a valid email'),
	password: z.string().min(8, 'Password must be at least 8 characters'),
	full_name: z.string().min(1, 'Full name is required')
});

export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;

/**
 * Auth user schema
 * Matches OpenAPI UserRead schema
 */
export const AuthUserSchema = z.object({
	id: z.string().uuid(),
	email: z.string().email(),
	full_name: z.string(),
	is_active: z.boolean(),
	is_verified: z.boolean(),
	is_superuser: z.boolean(),
	created_at: z.string() // Use string() instead of datetime() - backend may not include timezone
});

export type AuthUser = z.infer<typeof AuthUserSchema>;

// Type-level check to ensure Zod schema matches OpenAPI type
// This will cause a TypeScript error if the types diverge
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function _typeCheck(x: AuthUser): UserReadFromAPI {
	return x;
}
