/**
 * Transparency Page API Functions
 *
 * Issue #85: Frontend: Public Transparency Pages
 * EPIC #51: Transparency & Methodology Pages
 */

import { apiClient } from './client';
import type {
	TransparencyPage,
	TransparencyPageListResponse,
	TransparencyPageSlug
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
 * Valid transparency page slugs for navigation
 */
export const TRANSPARENCY_PAGE_SLUGS: TransparencyPageSlug[] = [
	'methodology',
	'organization',
	'team',
	'funding',
	'partnerships',
	'corrections-policy',
	'privacy-policy'
];

/**
 * Check if a slug is a valid transparency page slug
 */
export function isValidTransparencySlug(slug: string): slug is TransparencyPageSlug {
	return TRANSPARENCY_PAGE_SLUGS.includes(slug as TransparencyPageSlug);
}
