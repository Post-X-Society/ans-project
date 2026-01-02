import { apiClient } from './client';
import type {
	Submission,
	SubmissionCreate,
	SubmissionListResponse,
	SpotlightSubmissionCreate,
	SpotlightContent,
	UserBasic
} from './types';

/**
 * Create a new submission
 */
export async function createSubmission(data: SubmissionCreate): Promise<Submission> {
	const response = await apiClient.post<Submission>('/api/v1/submissions', data);
	return response.data;
}

/**
 * Create a new Spotlight submission
 */
export async function createSpotlightSubmission(
	data: SpotlightSubmissionCreate
): Promise<SpotlightContent> {
	const response = await apiClient.post<SpotlightContent>('/api/v1/submissions/spotlight', data);
	return response.data;
}

/**
 * Options for filtering submissions list
 */
export interface GetSubmissionsOptions {
	page?: number;
	page_size?: number;
	status?: 'pending' | 'processing' | 'completed';
	/**
	 * Filter to show only submissions assigned to current user
	 * Uses server-side filtering for optimal performance
	 */
	assigned_to_me?: boolean;
}

/**
 * Get list of submissions with pagination and optional filtering
 */
export async function getSubmissions(
	page: number = 1,
	page_size: number = 50,
	status?: 'pending' | 'processing' | 'completed',
	assigned_to_me?: boolean
): Promise<SubmissionListResponse> {
	const params: Record<string, any> = { page, page_size };
	if (status) {
		params.status = status;
	}
	if (assigned_to_me) {
		params.assigned_to_me = true;
	}
	const response = await apiClient.get<SubmissionListResponse>('/api/v1/submissions', {
		params
	});
	return response.data;
}

/**
 * Get a single submission by ID
 */
export async function getSubmission(id: string): Promise<Submission> {
	const response = await apiClient.get<Submission>(`/api/v1/submissions/${id}`);
	return response.data;
}

/**
 * Assign a reviewer to a submission
 */
export async function assignReviewer(
	submissionId: string,
	reviewerId: string
): Promise<{ message: string }> {
	const response = await apiClient.post<{ message: string }>(
		`/api/v1/submissions/${submissionId}/reviewers/${reviewerId}`
	);
	return response.data;
}

/**
 * Remove a reviewer from a submission
 */
export async function removeReviewer(
	submissionId: string,
	reviewerId: string
): Promise<{ message: string }> {
	const response = await apiClient.delete<{ message: string }>(
		`/api/v1/submissions/${submissionId}/reviewers/${reviewerId}`
	);
	return response.data;
}

/**
 * Get all reviewers assigned to a submission
 */
export async function getSubmissionReviewers(submissionId: string): Promise<UserBasic[]> {
	const response = await apiClient.get<UserBasic[]>(
		`/api/v1/submissions/${submissionId}/reviewers`
	);
	return response.data;
}
