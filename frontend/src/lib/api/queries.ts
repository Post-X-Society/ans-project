import type { QueryOptions, MutationOptions } from '@tanstack/svelte-query';
import { getSubmissions, getSubmission, createSubmission } from './submissions';
import { getTransparencyPages, getTransparencyPage } from './transparency';
import { getWorkflowHistory, getWorkflowCurrentState, transitionWorkflowState } from './workflow';
import {
	getSubmissionRatings,
	getCurrentRating,
	assignRating,
	getRatingDefinitions,
	type RatingAssignRequest
} from './ratings';
import type {
	SubmissionListResponse,
	Submission,
	SubmissionCreate,
	TransparencyPageListResponse,
	TransparencyPage,
	TransparencyPageSlug,
	WorkflowHistoryResponse,
	WorkflowCurrentStateResponse,
	WorkflowTransitionRequest,
	WorkflowHistoryItem,
	FactCheckRating,
	CurrentRatingResponse,
	RatingDefinitionListResponse
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

/**
 * Query options for fetching workflow history for a submission
 */
export function workflowHistoryQueryOptions(
	submissionId: string
): QueryOptions<WorkflowHistoryResponse> {
	return {
		queryKey: ['workflow', submissionId, 'history'],
		queryFn: () => getWorkflowHistory(submissionId),
		staleTime: 30 * 1000 // 30 seconds - workflow state can change
	};
}

/**
 * Query options for fetching current workflow state
 */
export function workflowCurrentStateQueryOptions(
	submissionId: string
): QueryOptions<WorkflowCurrentStateResponse> {
	return {
		queryKey: ['workflow', submissionId, 'current'],
		queryFn: () => getWorkflowCurrentState(submissionId),
		staleTime: 30 * 1000 // 30 seconds
	};
}

/**
 * Mutation options for workflow state transition
 */
export function workflowTransitionMutationOptions(
	submissionId: string
): MutationOptions<WorkflowHistoryItem, Error, WorkflowTransitionRequest> {
	return {
		mutationFn: (request: WorkflowTransitionRequest) =>
			transitionWorkflowState(submissionId, request)
	};
}

/**
 * Query options for fetching submission ratings (history)
 */
export function submissionRatingsQueryOptions(
	submissionId: string
): QueryOptions<FactCheckRating[]> {
	return {
		queryKey: ['submissions', submissionId, 'ratings'],
		queryFn: () => getSubmissionRatings(submissionId),
		staleTime: 30 * 1000 // 30 seconds
	};
}

/**
 * Query options for fetching current rating
 */
export function currentRatingQueryOptions(
	submissionId: string
): QueryOptions<CurrentRatingResponse> {
	return {
		queryKey: ['submissions', submissionId, 'ratings', 'current'],
		queryFn: () => getCurrentRating(submissionId),
		staleTime: 30 * 1000 // 30 seconds
	};
}

/**
 * Query options for fetching rating definitions
 */
export function ratingDefinitionsQueryOptions(): QueryOptions<RatingDefinitionListResponse> {
	return {
		queryKey: ['ratings', 'definitions'],
		queryFn: () => getRatingDefinitions(),
		staleTime: 5 * 60 * 1000 // 5 minutes - definitions rarely change
	};
}

/**
 * Mutation options for assigning a rating
 */
export function assignRatingMutationOptions(
	submissionId: string
): MutationOptions<FactCheckRating, Error, RatingAssignRequest> {
	return {
		mutationFn: (data: RatingAssignRequest) => assignRating(submissionId, data)
	};
}
