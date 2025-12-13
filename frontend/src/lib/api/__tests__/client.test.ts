import { describe, it, expect, beforeEach, vi } from 'vitest';
import { apiClient } from '../client';

describe('API Client', () => {
	beforeEach(() => {
		// Reset any mocks before each test
		vi.clearAllMocks();
	});

	it('should have the correct base URL from environment', () => {
		expect(apiClient.defaults.baseURL).toBeDefined();
		// Should use VITE_API_URL or default to localhost:8000
		expect(apiClient.defaults.baseURL).toMatch(/http/);
	});

	it('should have default headers set', () => {
		expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
	});

	it('should have a get method', () => {
		expect(apiClient.get).toBeDefined();
		expect(typeof apiClient.get).toBe('function');
	});

	it('should have a post method', () => {
		expect(apiClient.post).toBeDefined();
		expect(typeof apiClient.post).toBe('function');
	});

	it('should build correct URLs with base URL', () => {
		const url = apiClient.getUri({ url: '/api/v1/submissions' });
		expect(url).toContain('/api/v1/submissions');
	});
});
