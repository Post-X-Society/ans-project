import { redirect } from '@sveltejs/kit';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	if (browser) {
		const token = localStorage.getItem('ans_access_token');
		if (!token) {
			throw redirect(307, '/login?redirect=/submit');
		}
	}
	return {};
};
