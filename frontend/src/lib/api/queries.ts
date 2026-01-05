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
import { getDraft, saveDraft } from './drafts';
import { getPendingReviews, getPeerReviewStatus, submitPeerReview } from './peer-review';
import { getSources, createSource, updateSource, deleteSource } from './sources';
import { submitCorrectionRequest, getCorrectionsForFactCheck } from './corrections';
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
	RatingDefinitionListResponse,
	DraftResponse,
	DraftUpdate,
	PendingReviewsResponse,
	PeerReviewStatusResponse,
	PeerReviewSubmit,
	PeerReview,
	Source,
	SourceCreate,
	SourceUpdate,
	SourceListResponse,
	CorrectionCreate,
	CorrectionSubmitResponse,
	CorrectionListResponse
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
export function submissionQueryOptions(id: string, enabled: boolean = true): QueryOptions<Submission> {
	return {
		queryKey: ['submissions', id],
		queryFn: () => getSubmission(id),
		enabled: enabled && !!id
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
	submissionId: string,
	enabled: boolean = true
): QueryOptions<WorkflowHistoryResponse> {
	return {
		queryKey: ['workflow', submissionId, 'history'],
		queryFn: () => getWorkflowHistory(submissionId),
		staleTime: 30 * 1000, // 30 seconds - workflow state can change
		enabled: enabled && !!submissionId
	};
}

/**
 * Query options for fetching current workflow state
 */
export function workflowCurrentStateQueryOptions(
	submissionId: string,
	enabled: boolean = true
): QueryOptions<WorkflowCurrentStateResponse> {
	return {
		queryKey: ['workflow', submissionId, 'current'],
		queryFn: () => getWorkflowCurrentState(submissionId),
		staleTime: 30 * 1000, // 30 seconds
		enabled: enabled && !!submissionId
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
	submissionId: string,
	enabled: boolean = true
): QueryOptions<FactCheckRating[]> {
	return {
		queryKey: ['submissions', submissionId, 'ratings'],
		queryFn: () => getSubmissionRatings(submissionId),
		staleTime: 30 * 1000, // 30 seconds
		enabled: enabled && !!submissionId
	};
}

/**
 * Query options for fetching current rating
 */
export function currentRatingQueryOptions(
	submissionId: string,
	enabled: boolean = true
): QueryOptions<CurrentRatingResponse> {
	return {
		queryKey: ['submissions', submissionId, 'ratings', 'current'],
		queryFn: () => getCurrentRating(submissionId),
		staleTime: 30 * 1000, // 30 seconds
		enabled: enabled && !!submissionId
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

/**
 * Query options for fetching a fact-check draft
 */
export function draftQueryOptions(
	factCheckId: string,
	enabled: boolean = true
): QueryOptions<DraftResponse> {
	return {
		queryKey: ['fact-checks', factCheckId, 'draft'],
		queryFn: () => getDraft(factCheckId),
		staleTime: 30 * 1000, // 30 seconds
		enabled: enabled && !!factCheckId
	};
}

/**
 * Mutation options for saving a draft
 */
export function saveDraftMutationOptions(
	factCheckId: string
): MutationOptions<DraftResponse, Error, DraftUpdate> {
	return {
		mutationFn: (data: DraftUpdate) => saveDraft(factCheckId, data)
	};
}

/**
 * Query options for fetching pending peer reviews for the current user
 */
export function pendingReviewsQueryOptions(enabled: boolean = true): QueryOptions<PendingReviewsResponse> {
	return {
		queryKey: ['peer-reviews', 'pending'],
		queryFn: () => getPendingReviews(),
		staleTime: 30 * 1000, // 30 seconds - pending reviews can change
		enabled
	};
}

/**
 * Query options for fetching peer review status for a fact-check
 */
export function peerReviewStatusQueryOptions(
	factCheckId: string,
	minReviewers: number = 1,
	enabled: boolean = true
): QueryOptions<PeerReviewStatusResponse> {
	return {
		queryKey: ['peer-reviews', factCheckId, 'status', { minReviewers }],
		queryFn: () => getPeerReviewStatus(factCheckId, minReviewers),
		staleTime: 30 * 1000, // 30 seconds
		enabled: enabled && !!factCheckId
	};
}

/**
 * Mutation options for submitting a peer review decision
 */
export function submitPeerReviewMutationOptions(
	factCheckId: string
): MutationOptions<PeerReview, Error, PeerReviewSubmit> {
	return {
		mutationFn: (data: PeerReviewSubmit) => submitPeerReview(factCheckId, data)
	};
}

/**
 * Query options for fetching sources for a fact-check
 */
export function sourcesQueryOptions(
	factCheckId: string,
	enabled: boolean = true
): QueryOptions<SourceListResponse> {
	return {
		queryKey: ['fact-checks', factCheckId, 'sources'],
		queryFn: () => getSources(factCheckId),
		staleTime: 30 * 1000, // 30 seconds
		enabled: enabled && !!factCheckId
	};
}

/**
 * Mutation options for creating a source
 */
export function createSourceMutationOptions(
	factCheckId: string
): MutationOptions<Source, Error, SourceCreate> {
	return {
		mutationFn: (data: SourceCreate) => createSource(factCheckId, data)
	};
}

/**
 * Mutation options for updating a source
 */
export function updateSourceMutationOptions(
	factCheckId: string,
	sourceId: string
): MutationOptions<Source, Error, SourceUpdate> {
	return {
		mutationFn: (data: SourceUpdate) => updateSource(factCheckId, sourceId, data)
	};
}

/**
 * Mutation options for deleting a source
 */
export function deleteSourceMutationOptions(
	factCheckId: string,
	sourceId: string
): MutationOptions<void, Error, void> {
	return {
		mutationFn: () => deleteSource(factCheckId, sourceId)
	};
}

// =============================================================================
// Correction Request Query Options (Issue #79)
// =============================================================================

/**
 * Query options for fetching corrections for a fact-check
 */
export function correctionsForFactCheckQueryOptions(
	factCheckId: string,
	enabled: boolean = true
): QueryOptions<CorrectionListResponse> {
	return {
		queryKey: ['corrections', 'fact-check', factCheckId],
		queryFn: () => getCorrectionsForFactCheck(factCheckId),
		enabled: enabled && !!factCheckId
	};
}

/**
 * Mutation options for submitting a correction request
 */
export function submitCorrectionMutationOptions(): MutationOptions<
	CorrectionSubmitResponse,
	Error,
	CorrectionCreate
> {
	return {
		mutationFn: (data: CorrectionCreate) => submitCorrectionRequest(data)
	};
}
