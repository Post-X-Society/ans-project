/**
 * Correction API client functions
 * Issue #79: Frontend Correction Request Form (TDD)
 * Issue #80: Frontend Admin Correction Review Dashboard (TDD)
 * EPIC #50: Corrections & Complaints System
 *
 * Provides functions for:
 * - Submitting correction requests (public endpoint, no auth required)
 * - Admin correction review and triage (admin only)
 * - Applying corrections to fact-checks (admin only)
 */

import { apiClient } from './client';
import type {
	CorrectionCreate,
	CorrectionSubmitResponse,
	CorrectionListResponse,
	CorrectionPendingListResponse,
	CorrectionAllListResponse,
	CorrectionResponse,
	CorrectionReviewRequest,
	CorrectionApplyRequest,
	CorrectionApplicationResponse,
	CorrectionHistoryResponse,
	CorrectionStatus,
	CorrectionType,
	PublicLogListResponse
} from './types';

/**
 * Submit a correction request for a published fact-check.
 * This is a public endpoint - no authentication required.
 *
 * @param data - Correction request data
 * @returns CorrectionSubmitResponse with acknowledgment details
 */
export async function submitCorrectionRequest(
	data: CorrectionCreate
): Promise<CorrectionSubmitResponse> {
	const response = await apiClient.post<CorrectionSubmitResponse>('/api/v1/corrections', data);
	return response.data;
}

/**
 * Get corrections for a specific fact-check (public endpoint).
 *
 * @param factCheckId - UUID of the fact-check
 * @returns CorrectionListResponse with corrections array
 */
export async function getCorrectionsForFactCheck(
	factCheckId: string
): Promise<CorrectionListResponse> {
	const response = await apiClient.get<CorrectionListResponse>(
		`/api/v1/corrections/fact-check/${factCheckId}`
	);
	return response.data;
}

// =============================================================================
// Issue #80: Admin Correction Review Dashboard API Functions
// =============================================================================

/**
 * Get pending corrections for admin triage.
 * Returns corrections prioritized by type (substantial first) and age (older first).
 * Requires admin or super_admin role.
 *
 * @returns CorrectionPendingListResponse with corrections and overdue count
 */
export async function getPendingCorrections(): Promise<CorrectionPendingListResponse> {
	const response = await apiClient.get<CorrectionPendingListResponse>(
		'/api/v1/corrections/pending'
	);
	return response.data;
}

/**
 * List all corrections with optional filtering and pagination.
 * Requires admin or super_admin role.
 *
 * @param options - Filter and pagination options
 * @returns CorrectionAllListResponse with corrections and pagination info
 */
export async function getAllCorrections(options?: {
	status?: CorrectionStatus;
	correction_type?: CorrectionType;
	limit?: number;
	offset?: number;
}): Promise<CorrectionAllListResponse> {
	const params = new URLSearchParams();

	if (options?.status) {
		params.append('status', options.status);
	}
	if (options?.correction_type) {
		params.append('correction_type', options.correction_type);
	}
	if (options?.limit !== undefined) {
		params.append('limit', options.limit.toString());
	}
	if (options?.offset !== undefined) {
		params.append('offset', options.offset.toString());
	}

	const queryString = params.toString();
	const url = queryString ? `/api/v1/corrections?${queryString}` : '/api/v1/corrections';

	const response = await apiClient.get<CorrectionAllListResponse>(url);
	return response.data;
}

/**
 * Get a correction by ID.
 *
 * @param correctionId - UUID of the correction
 * @returns CorrectionResponse
 */
export async function getCorrectionById(correctionId: string): Promise<CorrectionResponse> {
	const response = await apiClient.get<CorrectionResponse>(
		`/api/v1/corrections/${correctionId}`
	);
	return response.data;
}

/**
 * Accept a pending correction request.
 * Requires admin or super_admin role.
 *
 * @param correctionId - UUID of the correction to accept
 * @param data - Review data with resolution notes
 * @returns Updated CorrectionResponse
 */
export async function acceptCorrection(
	correctionId: string,
	data: CorrectionReviewRequest
): Promise<CorrectionResponse> {
	const response = await apiClient.post<CorrectionResponse>(
		`/api/v1/corrections/${correctionId}/accept`,
		data
	);
	return response.data;
}

/**
 * Reject a pending correction request.
 * Requires admin or super_admin role.
 *
 * @param correctionId - UUID of the correction to reject
 * @param data - Review data with resolution notes
 * @returns Updated CorrectionResponse
 */
export async function rejectCorrection(
	correctionId: string,
	data: CorrectionReviewRequest
): Promise<CorrectionResponse> {
	const response = await apiClient.post<CorrectionResponse>(
		`/api/v1/corrections/${correctionId}/reject`,
		data
	);
	return response.data;
}

/**
 * Apply an accepted correction to a fact-check.
 * Creates a versioned record and updates the fact-check content.
 * Requires admin or super_admin role.
 *
 * @param correctionId - UUID of the correction to apply
 * @param data - Apply data with changes and summary
 * @returns CorrectionApplicationResponse with version info
 */
export async function applyCorrection(
	correctionId: string,
	data: CorrectionApplyRequest
): Promise<CorrectionApplicationResponse> {
	const response = await apiClient.post<CorrectionApplicationResponse>(
		`/api/v1/corrections/${correctionId}/apply`,
		data
	);
	return response.data;
}

/**
 * Get correction history for a fact-check.
 * Returns the full version history of corrections applied.
 *
 * @param factCheckId - UUID of the fact-check
 * @returns CorrectionHistoryResponse with all applications
 */
export async function getCorrectionHistory(
	factCheckId: string
): Promise<CorrectionHistoryResponse> {
	const response = await apiClient.get<CorrectionHistoryResponse>(
		`/api/v1/corrections/history/${factCheckId}`
	);
	return response.data;
}

/**
 * Get public corrections log.
 * Returns only accepted substantial and update corrections.
 * This is a public endpoint - no authentication required.
 *
 * @param options - Pagination options
 * @returns PublicLogListResponse
 */
export async function getPublicCorrectionsLog(options?: {
	limit?: number;
	offset?: number;
}): Promise<PublicLogListResponse> {
	const params = new URLSearchParams();

	if (options?.limit !== undefined) {
		params.append('limit', options.limit.toString());
	}
	if (options?.offset !== undefined) {
		params.append('offset', options.offset.toString());
	}

	const queryString = params.toString();
	const url = queryString
		? `/api/v1/corrections/public-log?${queryString}`
		: '/api/v1/corrections/public-log';

	const response = await apiClient.get<PublicLogListResponse>(url);
	return response.data;
}
