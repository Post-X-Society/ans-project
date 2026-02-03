import { apiClient } from './client';
import type { Source, SourceCreate, SourceUpdate, SourceListResponse } from './types';

/**
 * Get all sources for a fact-check
 */
export async function getSources(factCheckId: string): Promise<SourceListResponse> {
	const response = await apiClient.get<SourceListResponse>(
		`/api/v1/fact-checks/${factCheckId}/sources`
	);
	return response.data;
}

/**
 * Get a single source by ID
 */
export async function getSource(factCheckId: string, sourceId: string): Promise<Source> {
	const response = await apiClient.get<Source>(
		`/api/v1/fact-checks/${factCheckId}/sources/${sourceId}`
	);
	return response.data;
}

/**
 * Create a new source for a fact-check
 */
export async function createSource(factCheckId: string, data: SourceCreate): Promise<Source> {
	const response = await apiClient.post<Source>(
		`/api/v1/fact-checks/${factCheckId}/sources`,
		data
	);
	return response.data;
}

/**
 * Update an existing source
 */
export async function updateSource(
	factCheckId: string,
	sourceId: string,
	data: SourceUpdate
): Promise<Source> {
	const response = await apiClient.patch<Source>(
		`/api/v1/fact-checks/${factCheckId}/sources/${sourceId}`,
		data
	);
	return response.data;
}

/**
 * Delete a source
 */
export async function deleteSource(factCheckId: string, sourceId: string): Promise<void> {
	await apiClient.delete(`/api/v1/sources/${sourceId}`);
}
