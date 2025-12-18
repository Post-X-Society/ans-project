import axios, { type InternalAxiosRequestConfig } from 'axios';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';

// Get API URL from environment or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
	baseURL: API_URL,
	headers: {
		'Content-Type': 'application/json'
	},
	timeout: 10000 // 10 second timeout
});

// Helper to get access token from localStorage
function getAccessToken(): string | null {
	if (!browser) return null;
	return localStorage.getItem('ans_access_token');
}

// Helper to get refresh token from localStorage
function getRefreshToken(): string | null {
	if (!browser) return null;
	return localStorage.getItem('ans_refresh_token');
}

// Helper to update access token in localStorage
function updateAccessToken(token: string): void {
	if (!browser) return;
	localStorage.setItem('ans_access_token', token);
}

// Helper to clear auth data
function clearAuth(): void {
	if (!browser) return;
	localStorage.removeItem('ans_access_token');
	localStorage.removeItem('ans_refresh_token');
	localStorage.removeItem('ans_user');
}

// Track if we're currently refreshing to avoid multiple refresh requests
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

// Add subscribers waiting for token refresh
function subscribeTokenRefresh(callback: (token: string) => void) {
	refreshSubscribers.push(callback);
}

// Notify all subscribers when token is refreshed
function onTokenRefreshed(token: string) {
	refreshSubscribers.forEach((callback) => callback(token));
	refreshSubscribers = [];
}

// Only set up interceptors in browser environment
if (browser) {
	// Request interceptor - add auth token to requests
	apiClient.interceptors.request.use(
		(config: InternalAxiosRequestConfig) => {
			const token = getAccessToken();
			if (token && config.headers) {
				config.headers.Authorization = `Bearer ${token}`;
			}
			return config;
		},
		(error) => {
			return Promise.reject(error);
		}
	);

	// Response interceptor - handle 401 errors and token refresh
	apiClient.interceptors.response.use(
		(response) => response,
		async (error) => {
			const originalRequest = error.config;

			// Handle 401 Unauthorized
			if (error.response?.status === 401 && !originalRequest._retry) {
				// Don't try to refresh on auth endpoints
				if (
					originalRequest.url?.includes('/auth/login') ||
					originalRequest.url?.includes('/auth/register') ||
					originalRequest.url?.includes('/auth/refresh')
				) {
					return Promise.reject(error);
				}

				if (isRefreshing) {
					// If already refreshing, wait for the new token
					return new Promise((resolve) => {
						subscribeTokenRefresh((token: string) => {
							originalRequest.headers.Authorization = `Bearer ${token}`;
							resolve(apiClient(originalRequest));
						});
					});
				}

				originalRequest._retry = true;
				isRefreshing = true;

				const refreshToken = getRefreshToken();
				if (!refreshToken) {
					// No refresh token, redirect to login
					clearAuth();
					goto('/login');
					return Promise.reject(error);
				}

				try {
					// Attempt to refresh the token
					const response = await apiClient.post('/api/v1/auth/refresh', {
						refresh_token: refreshToken
					});

					const { access_token } = response.data;
					updateAccessToken(access_token);
					isRefreshing = false;
					onTokenRefreshed(access_token);

					// Retry original request with new token
					originalRequest.headers.Authorization = `Bearer ${access_token}`;
					return apiClient(originalRequest);
				} catch (refreshError) {
					// Refresh failed, logout user
					isRefreshing = false;
					clearAuth();
					goto('/login');
					return Promise.reject(refreshError);
				}
			}

			// Handle different error scenarios
			if (error.response) {
				// Server responded with error status
				console.error('API Error:', error.response.status, error.response.data);
			} else if (error.request) {
				// Request made but no response
				console.error('Network Error:', error.message);
			} else {
				// Something else happened
				console.error('Error:', error.message);
			}
			return Promise.reject(error);
		}
	);
}
