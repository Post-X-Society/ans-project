/**
 * Transparency Page API Functions
 *
 * Issue #85: Frontend: Public Transparency Pages
 * Issue #86: Frontend: Admin Transparency Page Editor
 * EPIC #51: Transparency & Methodology Pages
 */

import { apiClient } from './client';
import type {
	TransparencyPage,
	TransparencyPageListResponse,
	TransparencyPageSlug,
	TransparencyPageVersion,
	TransparencyPageDiff,
	TransparencyPageUpdate
} from './types';

/**
 * Fetch all transparency pages (list view)
 */
export async function getTransparencyPages(): Promise<TransparencyPageListResponse> {
	const response = await apiClient.get<TransparencyPageListResponse>('/api/v1/transparency');
	return response.data;
}

/**
 * Fetch a single transparency page by slug
 *
 * @param slug - The page slug (e.g., 'methodology', 'funding')
 * @param lang - Optional language code for filtering (e.g., 'en', 'nl')
 */
export async function getTransparencyPage(
	slug: TransparencyPageSlug | string,
	lang?: string
): Promise<TransparencyPage> {
	const params = lang ? { lang } : {};
	const response = await apiClient.get<TransparencyPage>(`/api/v1/transparency/${slug}`, {
		params
	});
	return response.data;
}

/**
 * Update a transparency page (admin only)
 *
 * @param slug - The page slug to update
 * @param data - Update payload with title, content, and change_summary
 */
export async function updateTransparencyPage(
	slug: TransparencyPageSlug | string,
	data: TransparencyPageUpdate
): Promise<TransparencyPage> {
	const response = await apiClient.patch<TransparencyPage>(`/api/v1/transparency/${slug}`, data);
	return response.data;
}

/**
 * Fetch version history for a transparency page
 *
 * @param slug - The page slug
 */
export async function getTransparencyPageVersions(
	slug: TransparencyPageSlug | string
): Promise<TransparencyPageVersion[]> {
	const response = await apiClient.get<TransparencyPageVersion[]>(
		`/api/v1/transparency/${slug}/versions`
	);
	return response.data;
}

/**
 * Get diff between two versions of a transparency page
 *
 * @param slug - The page slug
 * @param v1 - From version number
 * @param v2 - To version number
 * @param lang - Optional language code to filter diff
 */
export async function getTransparencyPageDiff(
	slug: TransparencyPageSlug | string,
	v1: number,
	v2: number,
	lang?: string
): Promise<TransparencyPageDiff> {
	const params = lang ? { lang } : {};
	const response = await apiClient.get<TransparencyPageDiff>(
		`/api/v1/transparency/${slug}/diff/${v1}/${v2}`,
		{ params }
	);
	return response.data;
}

/**
 * Mark a transparency page as reviewed (admin only)
 * This extends the next_review_due date by 1 year
 *
 * @param slug - The page slug to mark as reviewed
 */
export async function markTransparencyPageReviewed(
	slug: TransparencyPageSlug | string
): Promise<TransparencyPage> {
	const response = await apiClient.post<TransparencyPage>(`/api/v1/transparency/${slug}/review`);
	return response.data;
}

/**
 * Valid transparency page slugs for navigation
 */
export const TRANSPARENCY_PAGE_SLUGS: TransparencyPageSlug[] = [
	'methodology',
	'organization',
	'team',
	'funding',
	'partnerships',
	'corrections-policy',
	'privacy-policy',
	'terms'
];

/**
 * Check if a slug is a valid transparency page slug
 */
export function isValidTransparencySlug(slug: string): slug is TransparencyPageSlug {
	return TRANSPARENCY_PAGE_SLUGS.includes(slug as TransparencyPageSlug);
}
