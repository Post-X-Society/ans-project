/**
 * Page load function for EFCSN Compliance Dashboard.
 *
 * Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
 */

import type { PageLoad } from './$types';
import { getAnalyticsDashboard } from '$lib/api/analytics';

export const load: PageLoad = async () => {
	try {
		const dashboard = await getAnalyticsDashboard();
		return {
			dashboard,
			error: null
		};
	} catch (error) {
		console.error('Failed to load analytics dashboard:', error);
		return {
			dashboard: null,
			error: error instanceof Error ? error.message : 'Failed to load dashboard'
		};
	}
};
