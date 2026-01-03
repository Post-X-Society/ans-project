import { getSubmissions } from '$lib/api/submissions';
import { getPendingReviews } from '$lib/api/peer-review';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	// Fetch active assignments (assigned to current user, status = processing)
	const activeAssignments = await getSubmissions(1, 50, 'processing', true);

	// Fetch completed submissions (assigned to current user, status = completed, limit 10)
	const completedSubmissions = await getSubmissions(1, 10, 'completed', true);

	// Fetch pending peer reviews
	const pendingReviews = await getPendingReviews();

	return {
		activeAssignments,
		completedSubmissions,
		pendingReviews
	};
};
