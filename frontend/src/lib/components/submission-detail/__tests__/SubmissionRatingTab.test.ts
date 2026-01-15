import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale } from 'svelte-i18n';
import SubmissionRatingTab from '../SubmissionRatingTab.svelte';
import type {
	Submission,
	WorkflowCurrentStateResponse,
	FactCheckRating,
	CurrentRatingResponse,
	RatingDefinition,
	User
} from '$lib/api/types';

// Mock data
const mockSubmission: Submission = {
	id: 'test-submission-123',
	content: 'https://example.com/claim-to-verify',
	submission_type: 'spotlight',
	status: 'processing',
	user_id: 'user-1',
	created_at: '2024-01-15T10:30:00Z',
	updated_at: '2024-01-16T14:45:00Z',
	reviewers: []
};

const mockWorkflowState: WorkflowCurrentStateResponse = {
	submission_id: 'test-submission-123',
	current_state: 'in_research',
	valid_transitions: ['draft_ready', 'needs_more_research', 'rejected']
};

const mockCurrentRating: CurrentRatingResponse = {
	rating: {
		id: 'rating-1',
		fact_check_id: 'fc-1',
		rating: 'partly_false',
		justification: 'The claim contains some accurate information but key facts are incorrect.',
		assigned_by_id: 'admin-1',
		version: 1,
		is_current: true,
		created_at: '2024-01-16T10:00:00Z'
	},
	definition: {
		id: 'def-1',
		rating: 'partly_false',
		name: { en: 'Partly False', nl: 'Gedeeltelijk Onjuist' },
		description: { en: 'Contains some false information', nl: 'Bevat gedeeltelijk onjuiste informatie' },
		color_hex: '#FFA500',
		icon: 'warning',
		display_order: 2,
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z'
	}
};

const mockRatings: FactCheckRating[] = [
	{
		id: 'rating-1',
		fact_check_id: 'fc-1',
		rating: 'partly_false',
		justification: 'The claim contains some accurate information but key facts are incorrect.',
		assigned_by_id: 'admin-1',
		version: 1,
		is_current: true,
		created_at: '2024-01-16T10:00:00Z'
	}
];

const mockRatingDefinitions: RatingDefinition[] = [
	{
		id: 'def-1',
		rating: 'true',
		name: { en: 'True', nl: 'Waar' },
		description: { en: 'The claim is accurate', nl: 'De bewering is juist' },
		color_hex: '#00FF00',
		icon: 'check',
		display_order: 1,
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z'
	},
	{
		id: 'def-2',
		rating: 'false',
		name: { en: 'False', nl: 'Onjuist' },
		description: { en: 'The claim is false', nl: 'De bewering is onjuist' },
		color_hex: '#FF0000',
		icon: 'x',
		display_order: 2,
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z'
	}
];

const mockAdminUser: User = {
	id: 'admin-1',
	email: 'admin@example.com',
	role: 'admin',
	is_active: true,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

const mockReviewerUser: User = {
	id: 'reviewer-1',
	email: 'reviewer@example.com',
	role: 'reviewer',
	is_active: true,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('SubmissionRatingTab', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('Rating Assignment Form', () => {
		it('should show rating form for admin users', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			expect(screen.getByTestId('rating-form')).toBeInTheDocument();
		});

		it('should show rating form for reviewer users', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockReviewerUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			expect(screen.getByTestId('rating-form')).toBeInTheDocument();
		});

		it('should not show rating form when workflow state is published', () => {
			const publishedWorkflowState = {
				...mockWorkflowState,
				current_state: 'published' as const,
				valid_transitions: []
			};

			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: publishedWorkflowState,
					currentRating: mockCurrentRating,
					ratings: mockRatings,
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			expect(screen.queryByTestId('rating-form')).not.toBeInTheDocument();
		});

		it('should display rating options from definitions', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const select = screen.getByRole('combobox');
			expect(select).toBeInTheDocument();
		});

		it('should have justification textarea', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const textarea = screen.getByRole('textbox');
			expect(textarea).toBeInTheDocument();
		});

		it('should show character count for justification', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			// Should show 0/50 initially
			expect(screen.getByText(/0\/50/)).toBeInTheDocument();
		});
	});

	describe('Current Rating Display', () => {
		it('should display current rating when exists', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: mockCurrentRating,
					ratings: mockRatings,
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const ratingCard = screen.getByTestId('current-rating-card');
			expect(ratingCard).toBeInTheDocument();
		});

		it('should display rating justification', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: mockCurrentRating,
					ratings: mockRatings,
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			// Justification may appear in both current rating and history
			const justificationElements = screen.getAllByText('The claim contains some accurate information but key facts are incorrect.');
			expect(justificationElements.length).toBeGreaterThan(0);
		});

		it('should display rating timestamp', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: mockCurrentRating,
					ratings: mockRatings,
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			// There may be multiple timestamps (current rating + history)
			const timestampElements = screen.getAllByTestId('rating-timestamp');
			expect(timestampElements.length).toBeGreaterThan(0);
		});

		it('should show loading state for rating', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: true,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const ratingCard = screen.getByTestId('current-rating-card');
			expect(ratingCard).toBeInTheDocument();
		});

		it('should show no rating message when none exists', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: { rating: null, definition: null },
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const ratingCard = screen.getByTestId('current-rating-card');
			expect(ratingCard).toBeInTheDocument();
		});
	});

	describe('Workflow Transitions', () => {
		it('should display workflow transition panel for admin', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			// Issue #179: Now using WorkflowTransitionPanel component
			const transitionsPanel = screen.getByTestId('workflow-transition-panel');
			expect(transitionsPanel).toBeInTheDocument();
		});

		it('should call onTransitionClick when transition button clicked', async () => {
			const onTransitionClick = vi.fn();

			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick,
					isSubmittingRating: false
				}
			});

			// Issue #179: WorkflowTransitionPanel renders buttons by role
			const transitionButtons = screen.getAllByRole('button');
			// Filter to only transition buttons (excluding other buttons on the page)
			const draftReadyButton = screen.getByRole('button', { name: /draft ready/i });
			expect(draftReadyButton).toBeInTheDocument();

			await fireEvent.click(draftReadyButton);
			expect(onTransitionClick).toHaveBeenCalledWith('draft_ready');
		});

		it('should show workflow transition panel for reviewer with valid transitions', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockReviewerUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			// Issue #179: WorkflowTransitionPanel is now shown for all users with workflow state
			// The panel shows the current state and available transitions
			expect(screen.getByTestId('workflow-transition-panel')).toBeInTheDocument();
		});
	});

	describe('Rating History', () => {
		it('should display rating history when exists', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: mockCurrentRating,
					ratings: mockRatings,
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: false,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const historyCard = screen.getByTestId('rating-history-card');
			expect(historyCard).toBeInTheDocument();
		});

		it('should not display history card when no ratings', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			expect(screen.queryByTestId('rating-history-card')).not.toBeInTheDocument();
		});
	});

	describe('Layout', () => {
		it('should have responsive grid layout', () => {
			render(SubmissionRatingTab, {
				props: {
					submission: mockSubmission,
					submissionId: 'test-submission-123',
					workflowState: mockWorkflowState,
					currentRating: null,
					ratings: [],
					ratingDefinitions: mockRatingDefinitions,
					user: mockAdminUser,
					isLoadingRating: false,
					showFactCheckEditor: true,
					onRatingSubmit: vi.fn(),
					onTransitionClick: vi.fn(),
					isSubmittingRating: false
				}
			});

			const container = screen.getByTestId('rating-tab-container');
			expect(container).toHaveClass('grid');
			expect(container).toHaveClass('lg:grid-cols-3');
		});
	});
});
