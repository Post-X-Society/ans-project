import { apiClient } from './client';
import type {
	Submission,
	SubmissionCreate,
	SubmissionListResponse,
	SpotlightSubmissionCreate,
	SpotlightContent
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
 * Get list of submissions with pagination
 */
export async function getSubmissions(
	page: number = 1,
	page_size: number = 50
): Promise<SubmissionListResponse> {
	const response = await apiClient.get<SubmissionListResponse>('/api/v1/submissions', {
		params: { page, page_size }
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
