import { z } from 'zod';

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
 */
export const RegisterRequestSchema = z.object({
	email: z.string().email('Please enter a valid email'),
	password: z.string().min(8, 'Password must be at least 8 characters'),
	full_name: z.string().min(1, 'Full name is required')
});

export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;

/**
 * Auth user schema
 */
export const AuthUserSchema = z.object({
	id: z.string(),
	email: z.string().email(),
	full_name: z.string().optional(),
	is_active: z.boolean(),
	is_verified: z.boolean()
});

export type AuthUser = z.infer<typeof AuthUserSchema>;
