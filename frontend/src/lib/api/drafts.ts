import { apiClient } from './client';
import type { DraftResponse, DraftUpdate } from './types';

/**
 * Fetch the current draft for a fact-check
 */
export async function getDraft(factCheckId: string): Promise<DraftResponse> {
	const response = await apiClient.get<DraftResponse>(`/api/v1/fact-checks/${factCheckId}/draft`);
	return response.data;
}

/**
 * Save/update a draft for a fact-check
 */
export async function saveDraft(
	factCheckId: string,
	draftData: DraftUpdate
): Promise<DraftResponse> {
	const response = await apiClient.patch<DraftResponse>(
		`/api/v1/fact-checks/${factCheckId}/draft`,
		draftData
	);
	return response.data;
}
