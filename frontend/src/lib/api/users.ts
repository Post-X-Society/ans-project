import { apiClient } from './client';
import type { User, UserCreate, UserUpdate, UserRole } from './types';

/**
 * Get list of users (admin only)
 */
export async function getUsers(): Promise<User[]> {
	const response = await apiClient.get<User[]>('/api/v1/users');
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
