import type { QueryOptions, MutationOptions } from '@tanstack/svelte-query';
import { getSubmissions, getSubmission, createSubmission } from './submissions';
import type { SubmissionListResponse, Submission, SubmissionCreate } from './types';

/**
 * Query options for fetching list of submissions
 */
export function submissionsQueryOptions(
	page: number = 1,
	page_size: number = 50
): QueryOptions<SubmissionListResponse> {
	return {
		queryKey: ['submissions', { page, page_size }],
		queryFn: () => getSubmissions(page, page_size)
	};
}

/**
 * Query options for fetching a single submission
 */
export function submissionQueryOptions(id: string): QueryOptions<Submission> {
	return {
		queryKey: ['submissions', id],
		queryFn: () => getSubmission(id)
	};
}

/**
 * Mutation options for creating a submission
 */
export function createSubmissionMutationOptions(): MutationOptions<
	Submission,
	Error,
	SubmissionCreate
> {
	return {
		mutationFn: (data: SubmissionCreate) => createSubmission(data)
	};
}
