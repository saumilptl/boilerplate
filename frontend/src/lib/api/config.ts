import { PUBLIC_API_URL } from '$env/static/public';
import { base } from '$app/paths';

// API Base URL - uses environment variable or falls back to relative /api
export const API_BASE_URL = PUBLIC_API_URL || `${base}/api`;

// API Endpoints
export const ENDPOINTS = {
	AUTH: {
		LOGIN: '/auth/cookie/login',
		LOGOUT: '/auth/cookie/logout',
		ME: '/auth/users/me',
		REGISTER: '/auth/register'
	}
} as const;
