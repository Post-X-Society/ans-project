/**
 * Peer Review API Client
 *
 * Issue #67: Frontend: Peer Review Dashboard (TDD)
 * EPIC #48: Multi-Tier Approval & Peer Review
 * ADR 0005: EFCSN Compliance Architecture
 *
 * Provides API functions for:
 * - Getting pending peer reviews
 * - Getting peer review status/consensus
 * - Submitting peer review decisions
 */

import { apiClient } from './client';
import type {
	PendingReviewsResponse,
	PeerReviewStatusResponse,
	PeerReviewSubmit,
	PeerReview
} from './types';

/**
 * Get pending peer reviews for the current user
 */
export async function getPendingReviews(): Promise<PendingReviewsResponse> {
	const response = await apiClient.get<PendingReviewsResponse>('/api/v1/peer-review/pending');
	return response.data;
}

/**
 * Get peer review status/consensus for a fact-check
 */
export async function getPeerReviewStatus(
	factCheckId: string,
	minReviewers: number = 1
): Promise<PeerReviewStatusResponse> {
	const response = await apiClient.get<PeerReviewStatusResponse>(
		`/api/v1/peer-review/${factCheckId}/status`,
		{ params: { min_reviewers: minReviewers } }
	);
	return response.data;
}

/**
 * Submit a peer review decision (approve/reject)
 */
export async function submitPeerReview(
	factCheckId: string,
	data: PeerReviewSubmit
): Promise<PeerReview> {
	const response = await apiClient.post<PeerReview>(
		`/api/v1/peer-review/${factCheckId}/submit`,
		data
	);
	return response.data;
}
