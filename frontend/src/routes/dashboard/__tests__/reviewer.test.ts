import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { writable } from 'svelte/store';
import ReviewerDashboard from '../reviewer/+page.svelte';
import type { Submission, PendingReviewsResponse } from '$lib/api/types';
import * as authStore from '$lib/stores/auth';

// Mock the auth store
vi.mock('$lib/stores/auth', () => ({
	currentUser: writable(null)
}));

// Mock the API modules
vi.mock('$lib/api/submissions', () => ({
	getSubmissions: vi.fn()
}));

vi.mock('$lib/api/peer-review', () => ({
	getPendingReviews: vi.fn()
}));

describe('Reviewer Dashboard - TDD', () => {
	const mockActiveSubmissions: Submission[] = [
		{
			id: 'sub-1',
			user_id: 'user-1',
			content: 'Active claim 1',
			submission_type: 'text',
			status: 'processing',
			created_at: '2026-01-01T10:00:00Z',
			updated_at: '2026-01-01T10:00:00Z',
			reviewers: [{ id: 'current-user', email: 'reviewer@example.com' }],
			is_assigned_to_me: true,
			user: { id: 'user-1', email: 'submitter1@example.com' }
		},
		{
			id: 'sub-2',
			user_id: 'user-2',
			content: 'Active claim 2',
			submission_type: 'text',
			status: 'processing',
			created_at: '2026-01-02T10:00:00Z',
			updated_at: '2026-01-02T10:00:00Z',
			reviewers: [{ id: 'current-user', email: 'reviewer@example.com' }],
			is_assigned_to_me: true,
			user: { id: 'user-2', email: 'submitter2@example.com' }
		}
	];

	const mockCompletedSubmissions: Submission[] = [
		{
			id: 'sub-10',
			user_id: 'user-10',
			content: 'Completed claim 1',
			submission_type: 'text',
			status: 'completed',
			created_at: '2025-12-20T10:00:00Z',
			updated_at: '2025-12-28T10:00:00Z',
			reviewers: [{ id: 'current-user', email: 'reviewer@example.com' }],
			is_assigned_to_me: true,
			user: { id: 'user-10', email: 'submitter10@example.com' }
		}
	];

	const mockPendingReviews: PendingReviewsResponse = {
		pending_reviews: [
			{
				id: 'pr-1',
				fact_check_id: 'fc-1',
				reviewer_id: 'current-user',
				status: 'pending',
				requested_at: '2026-01-01T10:00:00Z',
				fact_check_title: 'Fact-check about climate',
				requester: {
					id: 'admin-1',
					email: 'admin@example.com',
					name: 'John Doe'
				},
				due_date: '2026-01-08T10:00:00Z'
			},
			{
				id: 'pr-2',
				fact_check_id: 'fc-2',
				reviewer_id: 'current-user',
				status: 'pending',
				requested_at: '2026-01-02T10:00:00Z',
				fact_check_title: 'Fact-check about health',
				requester: {
					id: 'admin-2',
					email: 'admin2@example.com',
					name: 'Mary Smith'
				},
				due_date: '2026-01-10T10:00:00Z'
			}
		],
		total: 2
	};

	beforeEach(() => {
		vi.clearAllMocks();
		authStore.currentUser.set({
			id: 'current-user',
			email: 'reviewer@example.com',
			role: 'reviewer'
		});
	});

	describe('Page Structure', () => {
		it('should render page title', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText('Reviewer Dashboard')).toBeInTheDocument();
		});

		it('should render all three sections', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			const { container } = render(ReviewerDashboard, { props: { data } });

			// Check for section headings (h2 elements)
			const headings = container.querySelectorAll('h2');
			const headingTexts = Array.from(headings).map((h) => h.textContent);

			expect(headingTexts).toContain('My Active Assignments (0)');
			expect(headingTexts).toContain('Pending Peer Reviews (0)');
			expect(headingTexts).toContain('Recently Completed (0)');
		});
	});

	describe('My Active Assignments Section', () => {
		it('should display count of active assignments in section header', () => {
			const data = {
				activeAssignments: {
					items: mockActiveSubmissions,
					total: 2,
					page: 1,
					page_size: 50,
					total_pages: 1
				},
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText(/my active assignments \(2\)/i)).toBeInTheDocument();
		});

		it('should render submission cards for active assignments', () => {
			const data = {
				activeAssignments: {
					items: mockActiveSubmissions,
					total: 2,
					page: 1,
					page_size: 50,
					total_pages: 1
				},
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText('Active claim 1')).toBeInTheDocument();
			expect(screen.getByText('Active claim 2')).toBeInTheDocument();
		});

		it('should show empty state when no active assignments', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(
				screen.getByText(/no active assignments/i, { exact: false })
			).toBeInTheDocument();
		});
	});

	describe('Pending Peer Reviews Section', () => {
		it('should display count of pending reviews in section header', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: mockPendingReviews
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText(/pending peer reviews \(2\)/i)).toBeInTheDocument();
		});

		it('should display pending review items with requester name', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: mockPendingReviews
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText(/fact-check about climate/i)).toBeInTheDocument();
			expect(screen.getByText(/john doe/i)).toBeInTheDocument();
			expect(screen.getByText(/fact-check about health/i)).toBeInTheDocument();
			expect(screen.getByText(/mary smith/i)).toBeInTheDocument();
		});

		it('should show empty state when no pending reviews', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText(/no pending peer reviews/i, { exact: false })).toBeInTheDocument();
		});
	});

	describe('Recently Completed Section', () => {
		it('should display count of completed submissions in section header', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: {
					items: mockCompletedSubmissions,
					total: 1,
					page: 1,
					page_size: 10,
					total_pages: 1
				},
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText(/recently completed \(1\)/i)).toBeInTheDocument();
		});

		it('should display completed submission items', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: {
					items: mockCompletedSubmissions,
					total: 1,
					page: 1,
					page_size: 10,
					total_pages: 1
				},
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(screen.getByText('Completed claim 1')).toBeInTheDocument();
		});

		it('should show empty state when no completed submissions', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			render(ReviewerDashboard, { props: { data } });

			expect(
				screen.getByText(/no completed submissions/i, { exact: false })
			).toBeInTheDocument();
		});
	});

	describe('Accessibility', () => {
		it('should have proper heading hierarchy', () => {
			const data = {
				activeAssignments: { items: [], total: 0, page: 1, page_size: 50, total_pages: 0 },
				completedSubmissions: { items: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
				pendingReviews: { pending_reviews: [], total: 0 }
			};

			const { container } = render(ReviewerDashboard, { props: { data } });

			const h1 = container.querySelector('h1');
			expect(h1).toBeInTheDocument();
			expect(h1).toHaveTextContent('Reviewer Dashboard');

			const h2s = container.querySelectorAll('h2');
			expect(h2s).toHaveLength(3); // Three sections
		});
	});
});
