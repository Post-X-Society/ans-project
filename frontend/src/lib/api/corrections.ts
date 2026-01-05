/**
 * Correction API client functions
 * Issue #79: Frontend Correction Request Form (TDD)
 * EPIC #50: Corrections & Complaints System
 *
 * Provides functions for submitting correction requests
 * on published fact-checks (public endpoint, no auth required).
 */

import { apiClient } from './client';
import type {
	CorrectionCreate,
	CorrectionSubmitResponse,
	CorrectionListResponse
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
	const response = await apiClient.post<CorrectionSubmitResponse>(
		'/api/v1/corrections',
		data
	);
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
