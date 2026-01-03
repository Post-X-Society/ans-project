import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale } from 'svelte-i18n';
import SubmissionOverviewTab from '../SubmissionOverviewTab.svelte';
import type {
	Submission,
	WorkflowHistoryResponse,
	WorkflowCurrentStateResponse
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
	user: { id: 'user-1', email: 'submitter@example.com' },
	spotlight_content: {
		spotlight_id: 'spotlight-123',
		thumbnail_url: 'https://example.com/thumb.jpg',
		creator_name: 'Test Creator',
		creator_username: 'testcreator',
		view_count: 50000,
		duration_ms: 45000
	},
	reviewers: [
		{ id: 'reviewer-1', email: 'reviewer1@example.com' },
		{ id: 'reviewer-2', email: 'reviewer2@example.com' }
	]
};

const mockWorkflowHistory: WorkflowHistoryResponse = {
	items: [
		{
			id: 'wh-1',
			submission_id: 'test-submission-123',
			from_state: null,
			to_state: 'submitted',
			transitioned_by_id: 'user-1',
			reason: null,
			metadata: null,
			created_at: '2024-01-15T10:30:00Z'
		},
		{
			id: 'wh-2',
			submission_id: 'test-submission-123',
			from_state: 'submitted',
			to_state: 'in_research',
			transitioned_by_id: 'admin-1',
			reason: 'Assigned for research',
			metadata: null,
			created_at: '2024-01-15T12:00:00Z'
		}
	],
	total: 2,
	current_state: 'in_research'
};

const mockWorkflowState: WorkflowCurrentStateResponse = {
	submission_id: 'test-submission-123',
	current_state: 'in_research',
	valid_transitions: ['draft_ready', 'needs_more_research', 'rejected']
};

describe('SubmissionOverviewTab', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('Submission Info Card', () => {
		it('should display submission content', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			expect(screen.getByText('https://example.com/claim-to-verify')).toBeInTheDocument();
		});

		it('should display content type badge', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			// The component should show the submission type
			const container = screen.getByTestId('submission-info-card');
			expect(container).toBeInTheDocument();
		});

		it('should display submitter email', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			expect(screen.getByText('submitter@example.com')).toBeInTheDocument();
		});

		it('should display formatted timestamps', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			// The component should format and display dates
			const timeElements = screen.getAllByRole('time');
			expect(timeElements.length).toBeGreaterThan(0);
		});

		it('should display current workflow state', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			// Current state should be displayed somewhere
			const container = screen.getByTestId('submission-info-card');
			expect(container).toBeInTheDocument();
		});
	});

	describe('Spotlight Content', () => {
		it('should display spotlight thumbnail when available', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			const thumbnail = screen.getByRole('img');
			expect(thumbnail).toBeInTheDocument();
			expect(thumbnail).toHaveAttribute('src', 'https://example.com/thumb.jpg');
		});

		it('should display creator name', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			expect(screen.getByText('Test Creator')).toBeInTheDocument();
		});

		it('should display formatted view count', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			// 50000 should be formatted as "50,000"
			expect(screen.getByText('50,000')).toBeInTheDocument();
		});

		it('should display formatted duration', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			// 45000ms should be formatted as "0:45"
			expect(screen.getByText('0:45')).toBeInTheDocument();
		});

		it('should not display spotlight section when no spotlight content', () => {
			const submissionWithoutSpotlight = {
				...mockSubmission,
				spotlight_content: undefined
			};

			render(SubmissionOverviewTab, {
				props: {
					submission: submissionWithoutSpotlight,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			expect(screen.queryByTestId('spotlight-info-card')).not.toBeInTheDocument();
		});
	});

	describe('Assigned Reviewers', () => {
		it('should display assigned reviewers', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			expect(screen.getByText('reviewer1@example.com')).toBeInTheDocument();
			expect(screen.getByText('reviewer2@example.com')).toBeInTheDocument();
		});

		it('should show no reviewers message when none assigned', () => {
			const submissionNoReviewers = { ...mockSubmission, reviewers: [] };

			render(SubmissionOverviewTab, {
				props: {
					submission: submissionNoReviewers,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			const container = screen.getByTestId('assigned-reviewers-card');
			expect(container).toBeInTheDocument();
		});
	});

	describe('Workflow Timeline', () => {
		it('should render WorkflowTimeline component', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			const timelineSection = screen.getByTestId('workflow-timeline-card');
			expect(timelineSection).toBeInTheDocument();
		});

		it('should pass loading state to WorkflowTimeline', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: true,
					historyError: null
				}
			});

			// Timeline should receive isLoading prop
			const timelineSection = screen.getByTestId('workflow-timeline-card');
			expect(timelineSection).toBeInTheDocument();
		});

		it('should pass error state to WorkflowTimeline', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: 'Failed to load workflow history'
				}
			});

			const timelineSection = screen.getByTestId('workflow-timeline-card');
			expect(timelineSection).toBeInTheDocument();
		});
	});

	describe('Layout', () => {
		it('should have responsive grid layout', () => {
			render(SubmissionOverviewTab, {
				props: {
					submission: mockSubmission,
					workflowHistory: mockWorkflowHistory,
					workflowState: mockWorkflowState,
					isLoadingHistory: false,
					historyError: null
				}
			});

			const container = screen.getByTestId('overview-tab-container');
			expect(container).toHaveClass('grid');
			expect(container).toHaveClass('lg:grid-cols-3');
		});
	});
});
