import { redirect } from '@sveltejs/kit';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	// Check authentication in browser
	if (browser) {
		const token = localStorage.getItem('ans_access_token');
		if (!token) {
			throw redirect(307, `/login?redirect=/submissions/${params.id}`);
		}
	}

	return {
		id: params.id
	};
};
