import { getSubmissions } from '$lib/api/submissions';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	// Fetch all submissions (we'll filter client-side by workflow_state)
	// Using large page_size to get all submissions for filtering
	const submissions = await getSubmissions(1, 100);

	return {
		submissions
	};
};
