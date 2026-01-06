/**
 * RTBF (Right to be Forgotten) API Client
 *
 * Issue #92: Backend: Right to be Forgotten Workflow (TDD)
 * EPIC #53: GDPR & Data Retention Compliance
 *
 * API functions for managing GDPR Article 17 deletion requests
 */

import { apiClient } from './client';
import type {
	RTBFRequest,
	RTBFRequestCreate,
	RTBFRequestListResponse,
	RTBFRequestProcessResult,
	DataExportResponse,
	UserDataSummary
} from './types';

/**
 * Create a new RTBF (Right to be Forgotten) deletion request
 */
export async function createRTBFRequest(data: RTBFRequestCreate): Promise<RTBFRequest> {
	const response = await apiClient.post<RTBFRequest>('/api/v1/rtbf/requests', data);
	return response.data;
}

/**
 * Get the current user's RTBF requests
 */
export async function getMyRTBFRequests(): Promise<RTBFRequest[]> {
	const response = await apiClient.get<RTBFRequest[]>('/api/v1/rtbf/requests/me');
	return response.data;
}

/**
 * Get all RTBF requests (admin only)
 */
export async function getAllRTBFRequests(params?: {
	status?: 'pending' | 'processing' | 'completed' | 'rejected';
	limit?: number;
	offset?: number;
}): Promise<RTBFRequestListResponse> {
	const response = await apiClient.get<RTBFRequestListResponse>('/api/v1/rtbf/requests', {
		params
	});
	return response.data;
}

/**
 * Get a specific RTBF request by ID
 */
export async function getRTBFRequest(requestId: string): Promise<RTBFRequest> {
	const response = await apiClient.get<RTBFRequest>(`/api/v1/rtbf/requests/${requestId}`);
	return response.data;
}

/**
 * Process an RTBF request (admin only)
 * This deletes/anonymizes the user's data
 */
export async function processRTBFRequest(requestId: string): Promise<RTBFRequestProcessResult> {
	const response = await apiClient.post<RTBFRequestProcessResult>(
		`/api/v1/rtbf/requests/${requestId}/process`
	);
	return response.data;
}

/**
 * Reject an RTBF request (admin only)
 */
export async function rejectRTBFRequest(
	requestId: string,
	reason: string
): Promise<RTBFRequest> {
	const response = await apiClient.post<RTBFRequest>(`/api/v1/rtbf/requests/${requestId}/reject`, {
		rejection_reason: reason
	});
	return response.data;
}

/**
 * Export user data (GDPR Article 20 - Data Portability)
 */
export async function exportUserData(): Promise<DataExportResponse> {
	const response = await apiClient.get<DataExportResponse>('/api/v1/rtbf/export');
	return response.data;
}

/**
 * Get summary of user data that will be deleted
 */
export async function getUserDataSummary(): Promise<UserDataSummary> {
	const response = await apiClient.get<UserDataSummary>('/api/v1/rtbf/summary');
	return response.data;
}
