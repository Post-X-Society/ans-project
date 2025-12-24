import type { QueryOptions, MutationOptions } from '@tanstack/svelte-query';
import { getSubmissions, getSubmission, createSubmission } from './submissions';
import { getTransparencyPages, getTransparencyPage } from './transparency';
import type {
	SubmissionListResponse,
	Submission,
	SubmissionCreate,
	TransparencyPageListResponse,
	TransparencyPage,
	TransparencyPageSlug
} from './types';

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

/**
 * Query options for fetching all transparency pages
 */
export function transparencyPagesQueryOptions(): QueryOptions<TransparencyPageListResponse> {
	return {
		queryKey: ['transparency-pages'],
		queryFn: () => getTransparencyPages(),
		staleTime: 5 * 60 * 1000 // 5 minutes - transparency pages don't change often
	};
}

/**
 * Query options for fetching a single transparency page by slug
 */
export function transparencyPageQueryOptions(
	slug: TransparencyPageSlug | string,
	lang?: string
): QueryOptions<TransparencyPage> {
	return {
		queryKey: ['transparency-pages', slug, lang],
		queryFn: () => getTransparencyPage(slug, lang),
		staleTime: 5 * 60 * 1000 // 5 minutes
	};
}
