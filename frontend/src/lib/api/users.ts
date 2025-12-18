import { apiClient } from './client';
import type { User, UserCreate, UserUpdate, UserListResponse, UserRole } from './types';

/**
 * Get list of users (admin only)
 */
export async function getUsers(page: number = 1, page_size: number = 50): Promise<UserListResponse> {
	const response = await apiClient.get<UserListResponse>('/api/v1/users', {
		params: { page, page_size }
	});
	return response.data;
}

/**
 * Create new user (admin only)
 */
export async function createUser(data: UserCreate): Promise<User> {
	const response = await apiClient.post<User>('/api/v1/users', data);
	return response.data;
}

/**
 * Update user role (admin only)
 */
export async function updateUserRole(userId: string, role: UserRole): Promise<User> {
	const response = await apiClient.patch<User>(`/api/v1/users/${userId}/role`, { role });
	return response.data;
}

/**
 * Update user (admin only)
 */
export async function updateUser(userId: string, data: UserUpdate): Promise<User> {
	const response = await apiClient.patch<User>(`/api/v1/users/${userId}`, data);
	return response.data;
}

/**
 * Delete user (super admin only)
 */
export async function deleteUser(userId: string): Promise<void> {
	await apiClient.delete(`/api/v1/users/${userId}`);
}
