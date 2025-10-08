import { z } from 'zod';
import { API_BASE_URL } from './config';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
	status: number;
	code?: string;

	constructor(message: string, status: number, code?: string) {
		super(message);
		this.status = status;
		this.code = code;
	}
}

/**
 * Options for API requests
 */
interface ApiOptions<T = unknown> {
	/** Zod schema for response validation */
	schema?: z.ZodType<T>;
	/** Additional headers */
	headers?: Record<string, string>;
	/** Query parameters */
	params?: Record<string, string | number | boolean | undefined>;
}

/**
 * Build URL with query parameters
 */
function buildUrl(
	endpoint: string,
	params?: Record<string, string | number | boolean | undefined>
): string {
	const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
	const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
	let fullPath = `${baseUrl}${path}`;

	if (params) {
		const searchParams = new URLSearchParams();
		Object.entries(params).forEach(([key, value]) => {
			if (value !== undefined) {
				searchParams.set(key, String(value));
			}
		});

		const queryString = searchParams.toString();
		if (queryString) {
			fullPath += `?${queryString}`;
		}
	}

	return fullPath;
}

/**
 * Handle response and validate with Zod if schema provided
 */
async function handleResponse<T>(response: Response, schema?: z.ZodType<T>): Promise<T> {
	if (!response.ok) {
		const errorData = await response.json().catch(() => ({}));
		const errorMessage = errorData.message || errorData.detail || 'Request failed';
		const errorCode = errorData.code;
		throw new ApiError(errorMessage, response.status, errorCode);
	}

	// Handle 204 No Content
	if (response.status === 204) {
		return undefined as T;
	}

	const data = await response.json();

	// Validate response data if schema provided
	if (schema) {
		try {
			return schema.parse(data);
		} catch (e) {
			if (e instanceof z.ZodError) {
				throw new ApiError('Response validation failed', response.status);
			}
			throw e;
		}
	}

	return data;
}

/**
 * Main request function
 */
async function request<T = unknown>(
	endpoint: string,
	options: ApiOptions<T> & { method: string; body?: unknown } = { method: 'GET' }
): Promise<T> {
	const { method, body, headers = {}, params, schema } = options;

	const url = buildUrl(endpoint, params);

	const requestHeaders: Record<string, string> = {
		'Content-Type': 'application/json',
		...headers
	};

	// Handle different body types
	let processedBody: string | URLSearchParams | undefined;
	if (body) {
		if (body instanceof URLSearchParams) {
			processedBody = body;
		} else {
			processedBody = JSON.stringify(body);
		}
	}

	const init: RequestInit = {
		method,
		headers: requestHeaders,
		credentials: 'include',
		body: processedBody
	};

	const response = await fetch(url, init);
	return handleResponse(response, schema);
}

/**
 * GET request
 */
export async function get<T = unknown>(endpoint: string, options: ApiOptions<T> = {}): Promise<T> {
	return request(endpoint, { ...options, method: 'GET' });
}

/**
 * POST request
 */
export async function post<T = unknown>(
	endpoint: string,
	data?: unknown,
	options: ApiOptions<T> = {}
): Promise<T> {
	return request(endpoint, { ...options, method: 'POST', body: data });
}

/**
 * PUT request
 */
export async function put<T = unknown>(
	endpoint: string,
	data?: unknown,
	options: ApiOptions<T> = {}
): Promise<T> {
	return request(endpoint, { ...options, method: 'PUT', body: data });
}

/**
 * DELETE request
 */
export async function del<T = unknown>(endpoint: string, options: ApiOptions<T> = {}): Promise<T> {
	return request(endpoint, { ...options, method: 'DELETE' });
}
