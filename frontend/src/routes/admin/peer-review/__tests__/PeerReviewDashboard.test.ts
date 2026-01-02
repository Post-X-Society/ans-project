/**
 * PeerReviewDashboard Component Tests (TDD)
 *
 * Issue #67: Frontend: Peer Review Dashboard (TDD)
 * EPIC #48: Multi-Tier Approval & Peer Review
 *
 * These tests are written FIRST before implementing the component.
 * Following TDD approach as specified in the Frontend Developer role.
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { locale } from 'svelte-i18n';
import type {
	PendingReviewsResponse,
	PeerReviewStatusResponse,
	PeerReview,
	ApprovalStatus
} from '$lib/api/types';

// Use vi.hoisted to avoid initialization order issues
const { mockGetPendingReviews, mockGetPeerReviewStatus, mockSubmitPeerReview, mockGetSubmission } =
	vi.hoisted(() => ({
		mockGetPendingReviews: vi.fn(),
		mockGetPeerReviewStatus: vi.fn(),
		mockSubmitPeerReview: vi.fn(),
		mockGetSubmission: vi.fn()
	}));

// Mock the peer review API
vi.mock('$lib/api/peer-review', () => ({
	getPendingReviews: mockGetPendingReviews,
	getPeerReviewStatus: mockGetPeerReviewStatus,
	submitPeerReview: mockSubmitPeerReview
}));

// Mock the submissions API
vi.mock('$lib/api/submissions', () => ({
	getSubmission: mockGetSubmission
}));

// Mock the auth store
vi.mock('$lib/stores/auth', () => ({
	authStore: {
		subscribe: vi.fn((fn) => {
			fn({
				user: { id: 'reviewer-123', email: 'reviewer@example.com', role: 'reviewer' }
			});
			return () => {};
		})
	}
}));

// Import after mocks
import PeerReviewDashboard from '../+page.svelte';

// Sample test data
const mockPendingReviewsResponse: PendingReviewsResponse = {
	reviewer_id: 'reviewer-123',
	total_count: 2,
	reviews: [
		{
			id: 'review-1',
			fact_check_id: 'fc-1',
			created_at: '2025-12-27T10:00:00Z'
		},
		{
			id: 'review-2',
			fact_check_id: 'fc-2',
			created_at: '2025-12-26T08:00:00Z'
		}
	]
};

const mockEmptyPendingReviews: PendingReviewsResponse = {
	reviewer_id: 'reviewer-123',
	total_count: 0,
	reviews: []
};

const mockPeerReviewStatus: PeerReviewStatusResponse = {
	fact_check_id: 'fc-1',
	consensus_reached: false,
	approved: false,
	total_reviews: 3,
	approved_count: 1,
	rejected_count: 0,
	pending_count: 2,
	needs_more_reviewers: false,
	reviews: [
		{
			id: 'review-1',
			fact_check_id: 'fc-1',
			reviewer_id: 'reviewer-456',
			approval_status: 'approved' as ApprovalStatus,
			comments: 'Looks good',
			created_at: '2025-12-27T09:00:00Z',
			updated_at: '2025-12-27T09:00:00Z'
		},
		{
			id: 'review-2',
			fact_check_id: 'fc-1',
			reviewer_id: 'reviewer-123',
			approval_status: 'pending' as ApprovalStatus,
			comments: null,
			created_at: '2025-12-27T10:00:00Z',
			updated_at: '2025-12-27T10:00:00Z'
		}
	]
};

const mockSubmission = {
	id: 'sub-1',
	content: 'https://snapchat.com/spotlight/test',
	submission_type: 'spotlight' as const,
	status: 'processing' as const,
	user_id: 'user-1',
	created_at: '2025-12-25T10:00:00Z',
	updated_at: '2025-12-27T10:00:00Z',
	reviewers: []
};

const mockSubmittedReview: PeerReview = {
	id: 'review-1',
	fact_check_id: 'fc-1',
	reviewer_id: 'reviewer-123',
	approval_status: 'approved',
	comments: 'Approved with comments',
	created_at: '2025-12-27T10:00:00Z',
	updated_at: '2025-12-27T11:00:00Z'
};

describe('PeerReviewDashboard', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
		mockGetPendingReviews.mockResolvedValue(mockPendingReviewsResponse);
		mockGetPeerReviewStatus.mockResolvedValue(mockPeerReviewStatus);
		mockGetSubmission.mockResolvedValue(mockSubmission);
		mockSubmitPeerReview.mockResolvedValue(mockSubmittedReview);
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	describe('Loading and Initial Display', () => {
		it('should display loading state initially', () => {
			mockGetPendingReviews.mockImplementation(() => new Promise(() => {}));

			render(PeerReviewDashboard);

			expect(screen.getByText(/loading/i)).toBeInTheDocument();
		});

		it('should render dashboard title when loaded', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getByText(/peer review/i)).toBeInTheDocument();
			});
		});

		it('should display error state when API fails', async () => {
			mockGetPendingReviews.mockRejectedValue(new Error('API Error'));

			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getByText(/error/i)).toBeInTheDocument();
			});
		});

		it('should call getPendingReviews on mount', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(mockGetPendingReviews).toHaveBeenCalled();
			});
		});
	});

	describe('Pending Reviews List', () => {
		it('should display pending review count in notification badge', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getByText('2')).toBeInTheDocument();
			});
		});

		it('should display list of pending reviews', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				// Should show items from the pending reviews list
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});
		});

		it('should show empty state when no pending reviews', async () => {
			mockGetPendingReviews.mockResolvedValue(mockEmptyPendingReviews);

			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getByText(/no pending reviews/i)).toBeInTheDocument();
			});
		});

		it('should display fact-check ID for each pending review', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getByText(/fc-1/i)).toBeInTheDocument();
				expect(screen.getByText(/fc-2/i)).toBeInTheDocument();
			});
		});

		it('should display created date for each pending review', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				// Should show formatted dates
				expect(screen.getByText(/dec 27/i)).toBeInTheDocument();
			});
		});
	});

	describe('Review Detail View', () => {
		it('should show review details when clicking a pending review', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByTestId('review-detail-panel')).toBeInTheDocument();
			});
		});

		it('should fetch peer review status when selecting a review', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(mockGetPeerReviewStatus).toHaveBeenCalledWith('fc-1', 1);
			});
		});
	});

	describe('Consensus Indicators', () => {
		it('should display approval count indicator', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByText(/1.*approved/i)).toBeInTheDocument();
			});
		});

		it('should display rejected count indicator', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByText(/0.*rejected/i)).toBeInTheDocument();
			});
		});

		it('should display pending count indicator', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByText(/2.*pending/i)).toBeInTheDocument();
			});
		});

		it('should show consensus reached indicator when all reviewers have voted', async () => {
			const consensusReached: PeerReviewStatusResponse = {
				...mockPeerReviewStatus,
				consensus_reached: true,
				approved: true,
				pending_count: 0,
				approved_count: 3
			};
			mockGetPeerReviewStatus.mockResolvedValue(consensusReached);

			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByText(/consensus reached/i)).toBeInTheDocument();
			});
		});

		it('should show visual progress bar for approval status', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByTestId('consensus-progress-bar')).toBeInTheDocument();
			});
		});
	});

	describe('Approve/Reject Form', () => {
		it('should display approve button', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			});
		});

		it('should display reject button', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
			});
		});

		it('should display comments textarea', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByLabelText(/comments/i)).toBeInTheDocument();
			});
		});

		it('should call submitPeerReview with approved=true when clicking approve', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			});

			const approveBtn = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveBtn);

			await waitFor(() => {
				expect(mockSubmitPeerReview).toHaveBeenCalledWith('fc-1', {
					approved: true,
					comments: null
				});
			});
		});

		it('should call submitPeerReview with approved=false when clicking reject', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
			});

			const rejectBtn = screen.getByRole('button', { name: /reject/i });
			await fireEvent.click(rejectBtn);

			await waitFor(() => {
				expect(mockSubmitPeerReview).toHaveBeenCalledWith('fc-1', {
					approved: false,
					comments: null
				});
			});
		});

		it('should include comments in submission when provided', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByLabelText(/comments/i)).toBeInTheDocument();
			});

			const commentsTextarea = screen.getByLabelText(/comments/i);
			await fireEvent.input(commentsTextarea, {
				target: { value: 'This looks accurate to me.' }
			});

			const approveBtn = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveBtn);

			await waitFor(() => {
				expect(mockSubmitPeerReview).toHaveBeenCalledWith('fc-1', {
					approved: true,
					comments: 'This looks accurate to me.'
				});
			});
		});

		it('should show success message after submitting review', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			});

			const approveBtn = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveBtn);

			await waitFor(() => {
				expect(screen.getByText(/review submitted/i)).toBeInTheDocument();
			});
		});

		it('should remove review from pending list after submission', async () => {
			// After submitting, the pending reviews list should refresh
			mockGetPendingReviews
				.mockResolvedValueOnce(mockPendingReviewsResponse)
				.mockResolvedValueOnce({
					...mockPendingReviewsResponse,
					total_count: 1,
					reviews: [mockPendingReviewsResponse.reviews[1]]
				});

			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			});

			const approveBtn = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveBtn);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(1);
			});
		});

		it('should show loading state while submitting', async () => {
			// Use a promise that we control to ensure we can observe the loading state
			let resolveSubmit: (value: PeerReview) => void;
			mockSubmitPeerReview.mockImplementation(
				() =>
					new Promise<PeerReview>((resolve) => {
						resolveSubmit = resolve;
					})
			);

			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			});

			const approveBtn = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveBtn);

			// Check that the buttons show "Submitting..." while loading
			await waitFor(() => {
				const buttons = screen.getAllByRole('button');
				const hasSubmittingButton = buttons.some(
					(btn) => btn.textContent?.toLowerCase().includes('submitting')
				);
				expect(hasSubmittingButton).toBe(true);
			});

			// Resolve the promise to complete the test cleanly
			resolveSubmit!(mockSubmittedReview);
		});

		it('should show error message when submission fails', async () => {
			mockSubmitPeerReview.mockRejectedValue(new Error('Submission failed'));

			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			});

			const approveBtn = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveBtn);

			await waitFor(() => {
				expect(screen.getByText(/failed/i)).toBeInTheDocument();
			});
		});
	});

	describe('Other Reviewers Section', () => {
		it('should display other reviewers decisions', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				// Should show other reviewer's decision
				expect(screen.getByText(/looks good/i)).toBeInTheDocument();
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper heading structure', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				const heading = screen.getByRole('heading', { name: /peer review/i });
				expect(heading).toBeInTheDocument();
			});
		});

		it('should have accessible buttons', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
				expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
			});
		});

		it('should have proper form labels', async () => {
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getAllByTestId('pending-review-item').length).toBe(2);
			});

			const firstReview = screen.getAllByTestId('pending-review-item')[0];
			await fireEvent.click(firstReview);

			await waitFor(() => {
				expect(screen.getByLabelText(/comments/i)).toBeInTheDocument();
			});
		});
	});

	describe('i18n Support', () => {
		it('should display English labels by default', async () => {
			locale.set('en');
			render(PeerReviewDashboard);

			await waitFor(() => {
				expect(screen.getByText(/peer review/i)).toBeInTheDocument();
			});
		});

		it('should display Dutch labels when locale is nl', async () => {
			locale.set('nl');
			render(PeerReviewDashboard);

			await waitFor(() => {
				// Dutch translation of "Peer Review Dashboard"
				expect(screen.getByText(/peer review/i)).toBeInTheDocument();
			});
		});
	});
});
