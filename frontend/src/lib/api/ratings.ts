import { apiClient } from './client';
import type {
	FactCheckRating,
	CurrentRatingResponse,
	RatingDefinitionListResponse,
	FactCheckRatingValue
} from './types';

/**
 * Request payload for assigning a rating
 */
export interface RatingAssignRequest {
	rating: FactCheckRatingValue;
	justification: string;
}

/**
 * Fetch all ratings for a submission (rating history)
 */
export async function getSubmissionRatings(submissionId: string): Promise<FactCheckRating[]> {
	const response = await apiClient.get<FactCheckRating[]>(
		`/api/v1/submissions/${submissionId}/ratings`
	);
	return response.data;
}

/**
 * Get the current rating for a submission
 */
export async function getCurrentRating(submissionId: string): Promise<CurrentRatingResponse> {
	const response = await apiClient.get<CurrentRatingResponse>(
		`/api/v1/submissions/${submissionId}/ratings/current`
	);
	return response.data;
}

/**
 * Assign a new rating to a submission
 */
export async function assignRating(
	submissionId: string,
	data: RatingAssignRequest
): Promise<FactCheckRating> {
	const response = await apiClient.post<FactCheckRating>(
		`/api/v1/submissions/${submissionId}/ratings`,
		data
	);
	return response.data;
}

/**
 * Get all rating definitions
 */
export async function getRatingDefinitions(): Promise<RatingDefinitionListResponse> {
	const response = await apiClient.get<RatingDefinitionListResponse>('/api/v1/ratings/definitions');
	return response.data;
}
