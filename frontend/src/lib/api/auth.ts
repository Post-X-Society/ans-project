import { apiClient } from './client';
import type {
	LoginRequest,
	LoginResponse,
	RegisterRequest,
	RefreshRequest,
	AuthTokens,
	User
} from './types';

/**
 * Login with email and password
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
	const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', credentials);
	return response.data;
}

/**
 * Register new user
 */
export async function register(data: RegisterRequest): Promise<LoginResponse> {
	const response = await apiClient.post<LoginResponse>('/api/v1/auth/register', data);
	return response.data;
}

/**
 * Refresh access token
 */
export async function refreshAccessToken(refreshToken: string): Promise<AuthTokens> {
	const response = await apiClient.post<AuthTokens>('/api/v1/auth/refresh', {
		refresh_token: refreshToken
	});
	return response.data;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
	await apiClient.post('/api/v1/auth/logout');
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
	const response = await apiClient.get<User>('/api/v1/auth/me');
	return response.data;
}
