import { redirect } from '@sveltejs/kit';
import { browser } from '$app/environment';
import { getSubmissions } from '$lib/api/submissions';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	// Check authentication in browser
	if (browser) {
		const token = localStorage.getItem('ans_access_token');
		if (!token) {
			throw redirect(307, '/login?redirect=/submissions');
		}
	}

	// Fetch initial submissions data
	try {
		const data = await getSubmissions(1, 50);
		return {
			submissions: data
		};
	} catch (error) {
		console.error('Error loading submissions:', error);
		// Return empty data structure on error - the component will handle it
		return {
			submissions: {
				items: [],
				total: 0,
				page: 1,
				page_size: 50,
				total_pages: 0
			}
		};
	}
};
