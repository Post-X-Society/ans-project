import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale, waitLocale } from 'svelte-i18n';
import WorkflowTimeline from '../WorkflowTimeline.svelte';
import type { WorkflowHistoryItem, WorkflowState, PeerReviewStatusResponse, PeerReview } from '$lib/api/types';

// Mock data for testing
const mockHistoryItems: WorkflowHistoryItem[] = [
	{
		id: '1',
		submission_id: 'sub-123',
		from_state: null,
		to_state: 'submitted',
		transitioned_by_id: 'user-1',
		transitioned_by: { id: 'user-1', email: 'submitter@example.com' },
		reason: null,
		metadata: null,
		created_at: '2025-01-15T10:00:00Z'
	},
	{
		id: '2',
		submission_id: 'sub-123',
		from_state: 'submitted',
		to_state: 'queued',
		transitioned_by_id: 'system',
		transitioned_by: { id: 'system', email: 'system@ans.nl' },
		reason: 'Automatically queued for review',
		metadata: null,
		created_at: '2025-01-15T10:01:00Z'
	},
	{
		id: '3',
		submission_id: 'sub-123',
		from_state: 'queued',
		to_state: 'assigned',
		transitioned_by_id: 'user-2',
		transitioned_by: { id: 'user-2', email: 'admin@example.com' },
		reason: 'Assigned to reviewer',
		metadata: null,
		created_at: '2025-01-15T11:00:00Z'
	},
	{
		id: '4',
		submission_id: 'sub-123',
		from_state: 'assigned',
		to_state: 'in_research',
		transitioned_by_id: 'user-3',
		transitioned_by: { id: 'user-3', email: 'reviewer@example.com' },
		reason: 'Starting research',
		metadata: null,
		created_at: '2025-01-15T14:00:00Z'
	}
];

describe('WorkflowTimeline', () => {
	beforeEach(() => {
		locale.set('en');
	});

	describe('rendering', () => {
		it('should render the timeline container with correct role', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const timeline = screen.getByRole('list');
			expect(timeline).toBeInTheDocument();
			expect(timeline).toHaveAttribute('aria-label');
		});

		it('should render all transition items', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const items = screen.getAllByRole('listitem');
			expect(items).toHaveLength(mockHistoryItems.length);
		});

		it('should display state names for each transition', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			// Check that state names are displayed in the state badges
			// Use getAllByText since some words may appear in both state badges and reasons
			const submittedElements = screen.getAllByText(/submitted/i);
			expect(submittedElements.length).toBeGreaterThan(0);

			const queuedElements = screen.getAllByText(/queued/i);
			expect(queuedElements.length).toBeGreaterThan(0);

			const assignedElements = screen.getAllByText(/assigned/i);
			expect(assignedElements.length).toBeGreaterThan(0);

			const inResearchElements = screen.getAllByText(/in research/i);
			expect(inResearchElements.length).toBeGreaterThan(0);
		});

		it('should display actor emails for each transition', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			expect(screen.getByText(/submitter@example.com/i)).toBeInTheDocument();
			expect(screen.getByText(/admin@example.com/i)).toBeInTheDocument();
			expect(screen.getByText(/reviewer@example.com/i)).toBeInTheDocument();
		});

		it('should display transition reasons when provided', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			expect(screen.getByText(/Automatically queued for review/i)).toBeInTheDocument();
			expect(screen.getByText(/Assigned to reviewer/i)).toBeInTheDocument();
			expect(screen.getByText(/Starting research/i)).toBeInTheDocument();
		});

		it('should display timestamps for each transition', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			// Check that timestamps are present (format depends on locale)
			const timeElements = screen.getAllByRole('time');
			expect(timeElements).toHaveLength(mockHistoryItems.length);
		});
	});

	describe('chronological order', () => {
		it('should display transitions in chronological order (oldest first)', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const items = screen.getAllByRole('listitem');

			// First item should be 'submitted', last should be 'in_research'
			expect(items[0]).toHaveTextContent(/submitted/i);
			expect(items[items.length - 1]).toHaveTextContent(/in research/i);
		});
	});

	describe('current state highlighting', () => {
		it('should visually highlight the current active state', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const items = screen.getAllByRole('listitem');
			const currentItem = items[items.length - 1];

			// The current state item should have a special styling class
			expect(currentItem.className).toContain('current');
		});

		it('should mark the current state with aria-current', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const items = screen.getAllByRole('listitem');
			const currentItem = items[items.length - 1];

			expect(currentItem).toHaveAttribute('aria-current', 'step');
		});

		it('should not mark non-current items with aria-current', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const items = screen.getAllByRole('listitem');

			// All items except the last should not have aria-current
			for (let i = 0; i < items.length - 1; i++) {
				expect(items[i]).not.toHaveAttribute('aria-current', 'step');
			}
		});
	});

	describe('visual timeline elements', () => {
		it('should render connecting lines between states', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			// Check for timeline line elements (visual connectors)
			const timeline = screen.getByRole('list');
			expect(timeline.className).toContain('timeline');
		});

		it('should render state icons/indicators', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			// Each item should have an indicator element
			const items = screen.getAllByRole('listitem');
			items.forEach((item) => {
				const indicator = item.querySelector('[data-testid="timeline-indicator"]');
				expect(indicator).toBeInTheDocument();
			});
		});
	});

	describe('empty state', () => {
		it('should display empty message when no history is provided', () => {
			render(WorkflowTimeline, {
				props: {
					history: [],
					currentState: 'submitted'
				}
			});

			expect(screen.getByText(/no workflow history/i)).toBeInTheDocument();
		});
	});

	describe('loading state', () => {
		it('should display loading indicator when isLoading is true', () => {
			render(WorkflowTimeline, {
				props: {
					history: [],
					currentState: 'submitted',
					isLoading: true
				}
			});

			expect(screen.getByText(/loading/i)).toBeInTheDocument();
		});
	});

	describe('error state', () => {
		it('should display error message when error is provided', () => {
			render(WorkflowTimeline, {
				props: {
					history: [],
					currentState: 'submitted',
					error: 'Failed to load workflow history'
				}
			});

			expect(screen.getByText(/failed to load workflow history/i)).toBeInTheDocument();
		});
	});

	describe('multilingual support', () => {
		it('should display state names in English', () => {
			locale.set('en');
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems.slice(0, 1),
					currentState: 'submitted'
				}
			});

			expect(screen.getByText(/submitted/i)).toBeInTheDocument();
		});

		it('should display state names in Dutch when locale is nl', async () => {
			locale.set('nl');
			await waitLocale();

			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems.slice(0, 1),
					currentState: 'submitted'
				}
			});

			// Should show Dutch translation for 'submitted'
			await waitFor(() => {
				expect(screen.getByText(/ingediend/i)).toBeInTheDocument();
			});
		});
	});

	describe('accessibility', () => {
		it('should have accessible list with aria-label', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const timeline = screen.getByRole('list');
			expect(timeline).toHaveAttribute('aria-label');
		});

		it('should have descriptive labels for screen readers', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			// Time elements should have datetime attributes for accessibility
			const timeElements = screen.getAllByRole('time');
			timeElements.forEach((time) => {
				expect(time).toHaveAttribute('datetime');
			});
		});
	});

	describe('responsive design', () => {
		it('should have responsive classes applied', () => {
			render(WorkflowTimeline, {
				props: {
					history: mockHistoryItems,
					currentState: 'in_research'
				}
			});

			const timeline = screen.getByRole('list');
			// Check for responsive Tailwind classes
			expect(timeline.className).toMatch(/space-y-|gap-/);
		});
	});

	describe('state color coding', () => {
		const stateColors: Array<{ state: WorkflowState; expectedClass: string }> = [
			{ state: 'submitted', expectedClass: 'bg-blue' },
			{ state: 'queued', expectedClass: 'bg-gray' },
			{ state: 'assigned', expectedClass: 'bg-indigo' },
			{ state: 'in_research', expectedClass: 'bg-yellow' },
			{ state: 'published', expectedClass: 'bg-green' },
			{ state: 'rejected', expectedClass: 'bg-red' }
		];

		stateColors.forEach(({ state, expectedClass }) => {
			it(`should render ${state} with ${expectedClass} indicator`, () => {
				const singleItemHistory: WorkflowHistoryItem[] = [
					{
						id: '1',
						submission_id: 'sub-123',
						from_state: null,
						to_state: state,
						transitioned_by_id: 'user-1',
						transitioned_by: { id: 'user-1', email: 'test@example.com' },
						reason: null,
						metadata: null,
						created_at: '2025-01-15T10:00:00Z'
					}
				];

				render(WorkflowTimeline, {
					props: {
						history: singleItemHistory,
						currentState: state
					}
				});

				const indicator = screen.getByTestId('timeline-indicator');
				expect(indicator.className).toContain(expectedClass);
			});
		});
	});

	// =============================================================================
	// Issue #68: Peer Review Timeline Section Tests
	// =============================================================================

	describe('peer review section', () => {
		// Mock peer review data
		const mockPeerReviews: PeerReview[] = [
			{
				id: 'pr-1',
				fact_check_id: 'fc-123',
				reviewer_id: 'user-1',
				reviewer: { id: 'user-1', email: 'reviewer1@example.com' },
				approval_status: 'approved',
				comments: 'Well researched and accurate sources.',
				created_at: '2025-01-15T14:00:00Z',
				updated_at: '2025-01-15T14:00:00Z'
			},
			{
				id: 'pr-2',
				fact_check_id: 'fc-123',
				reviewer_id: 'user-2',
				reviewer: { id: 'user-2', email: 'reviewer2@example.com' },
				approval_status: 'approved',
				comments: 'Agree with the conclusion.',
				created_at: '2025-01-15T14:30:00Z',
				updated_at: '2025-01-15T14:30:00Z'
			},
			{
				id: 'pr-3',
				fact_check_id: 'fc-123',
				reviewer_id: 'user-3',
				reviewer: { id: 'user-3', email: 'reviewer3@example.com' },
				approval_status: 'pending',
				comments: null,
				created_at: '2025-01-15T15:00:00Z',
				updated_at: '2025-01-15T15:00:00Z'
			}
		];

		const mockPeerReviewStatus: PeerReviewStatusResponse = {
			fact_check_id: 'fc-123',
			consensus_reached: false,
			approved: false,
			total_reviews: 3,
			approved_count: 2,
			rejected_count: 0,
			pending_count: 1,
			needs_more_reviewers: false,
			reviews: mockPeerReviews
		};

		const mockPeerReviewConsensusReached: PeerReviewStatusResponse = {
			fact_check_id: 'fc-123',
			consensus_reached: true,
			approved: true,
			total_reviews: 3,
			approved_count: 3,
			rejected_count: 0,
			pending_count: 0,
			needs_more_reviewers: false,
			reviews: mockPeerReviews.map((r) => ({ ...r, approval_status: 'approved' as const }))
		};

		const peerReviewHistoryItems: WorkflowHistoryItem[] = [
			...mockHistoryItems,
			{
				id: '5',
				submission_id: 'sub-123',
				from_state: 'in_research',
				to_state: 'peer_review',
				transitioned_by_id: 'user-2',
				transitioned_by: { id: 'user-2', email: 'admin@example.com' },
				reason: 'Submitted for peer review',
				metadata: null,
				created_at: '2025-01-15T16:00:00Z'
			}
		];

		describe('peer review section visibility', () => {
			it('should display peer review section when peerReviewStatus is provided and current state is peer_review', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				expect(screen.getByTestId('peer-review-section')).toBeInTheDocument();
			});

			it('should not display peer review section when peerReviewStatus is not provided', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review'
					}
				});

				expect(screen.queryByTestId('peer-review-section')).not.toBeInTheDocument();
			});

			it('should display peer review section title', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				// Use heading role to specifically target the section title
				expect(screen.getByRole('heading', { name: /peer review/i })).toBeInTheDocument();
			});
		});

		describe('displaying reviewers and their decisions', () => {
			it('should display all reviewer emails', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				expect(screen.getByText(/reviewer1@example.com/i)).toBeInTheDocument();
				expect(screen.getByText(/reviewer2@example.com/i)).toBeInTheDocument();
				expect(screen.getByText(/reviewer3@example.com/i)).toBeInTheDocument();
			});

			it('should display approval status for each reviewer', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				// Should have review cards with status badges
				const reviewCards = screen.getAllByTestId('peer-review-card');
				expect(reviewCards).toHaveLength(3);

				// Check the summary has the right counts
				const summary = screen.getByTestId('peer-review-summary');
				expect(summary).toHaveTextContent(/2 approved/i);
				expect(summary).toHaveTextContent(/1 pending/i);
			});

			it('should display review counts summary', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				// Should show counts in some format (e.g., "2 approved, 0 rejected, 1 pending")
				expect(screen.getByTestId('peer-review-summary')).toBeInTheDocument();
			});

			it('should display rejected status when reviewer rejects', () => {
				const rejectedReview: PeerReviewStatusResponse = {
					...mockPeerReviewStatus,
					rejected_count: 1,
					approved_count: 1,
					reviews: [
						{
							...mockPeerReviews[0],
							approval_status: 'rejected',
							comments: 'Sources are not reliable.'
						},
						mockPeerReviews[1],
						mockPeerReviews[2]
					]
				};

				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: rejectedReview
					}
				});

				// Check that the summary includes rejected count
				const summary = screen.getByTestId('peer-review-summary');
				expect(summary).toHaveTextContent(/1 rejected/i);
			});
		});

		describe('displaying deliberation comments', () => {
			it('should display comments when reviewer has provided them', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				expect(screen.getByText(/Well researched and accurate sources/i)).toBeInTheDocument();
				expect(screen.getByText(/Agree with the conclusion/i)).toBeInTheDocument();
			});

			it('should not display comments section for reviewers without comments', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				// Reviewer 3 has no comments - should not show empty comment section
				const reviewCards = screen.getAllByTestId('peer-review-card');
				const reviewer3Card = reviewCards.find(
					(card) => card.textContent?.includes('reviewer3@example.com')
				);
				expect(reviewer3Card).toBeInTheDocument();
				// The card should not contain a comment text
				expect(reviewer3Card?.querySelector('[data-testid="review-comment"]')).toBeNull();
			});
		});

		describe('highlighting consensus', () => {
			it('should highlight when consensus is reached', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewConsensusReached
					}
				});

				const consensusBadge = screen.getByTestId('consensus-badge');
				expect(consensusBadge).toBeInTheDocument();
				expect(consensusBadge).toHaveTextContent(/consensus reached/i);
			});

			it('should show consensus badge with approved styling when all approve', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewConsensusReached
					}
				});

				const consensusBadge = screen.getByTestId('consensus-badge');
				expect(consensusBadge.className).toContain('bg-green');
			});

			it('should not show consensus badge when consensus not reached', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				expect(screen.queryByTestId('consensus-badge')).not.toBeInTheDocument();
			});

			it('should show pending indicator when reviews are still pending', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				expect(screen.getByTestId('awaiting-reviews-indicator')).toBeInTheDocument();
			});
		});

		describe('peer review loading state', () => {
			it('should show loading state when peerReviewLoading is true', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewLoading: true
					}
				});

				expect(screen.getByText(/loading peer reviews/i)).toBeInTheDocument();
			});
		});

		describe('peer review multilingual support', () => {
			it('should display peer review section in English', () => {
				locale.set('en');
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewConsensusReached
					}
				});

				// Use heading role to specifically target the section title
				expect(screen.getByRole('heading', { name: /peer review/i })).toBeInTheDocument();
				expect(screen.getByTestId('consensus-badge')).toHaveTextContent(/consensus reached/i);
			});

			it('should display peer review section in Dutch when locale is nl', async () => {
				locale.set('nl');
				await waitLocale();

				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewConsensusReached
					}
				});

				await waitFor(() => {
					// Use heading role to specifically target the section title
					expect(screen.getByRole('heading', { name: /collegiale toetsing/i })).toBeInTheDocument();
					expect(screen.getByTestId('consensus-badge')).toHaveTextContent(/consensus bereikt/i);
				});
			});
		});

		describe('accessibility for peer review section', () => {
			it('should have accessible region for peer review section', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				const peerReviewSection = screen.getByTestId('peer-review-section');
				expect(peerReviewSection).toHaveAttribute('role', 'region');
				expect(peerReviewSection).toHaveAttribute('aria-label');
			});

			it('should have accessible list for reviewers', () => {
				render(WorkflowTimeline, {
					props: {
						history: peerReviewHistoryItems,
						currentState: 'peer_review',
						peerReviewStatus: mockPeerReviewStatus
					}
				});

				const reviewersList = screen.getByTestId('peer-reviewers-list');
				expect(reviewersList).toHaveAttribute('role', 'list');
			});
		});
	});
});
