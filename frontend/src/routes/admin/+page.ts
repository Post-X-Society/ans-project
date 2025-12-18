import { redirect } from '@sveltejs/kit';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	if (browser) {
		const token = localStorage.getItem('ans_access_token');
		const userStr = localStorage.getItem('ans_user');

		if (!token) {
			throw redirect(307, '/login?redirect=/admin');
		}

		if (userStr) {
			const user = JSON.parse(userStr);
			// Backend returns lowercase role values
			if (user.role !== 'admin' && user.role !== 'super_admin') {
				throw redirect(307, '/');
			}
		}
	}
	return {};
};
