import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest';
import { locale } from 'svelte-i18n';
import { QueryClient } from '@tanstack/svelte-query';
import type {
	Submission,
	WorkflowHistoryResponse,
	WorkflowCurrentStateResponse,
	FactCheckRating,
	WorkflowState
} from '$lib/api/types';

// Mock the API modules
vi.mock('$lib/api/submissions', () => ({
	getSubmission: vi.fn()
}));

vi.mock('$lib/api/workflow', () => ({
	getWorkflowHistory: vi.fn(),
	getWorkflowCurrentState: vi.fn(),
	transitionWorkflowState: vi.fn()
}));

vi.mock('$lib/api/ratings', () => ({
	getSubmissionRatings: vi.fn(),
	getCurrentRating: vi.fn(),
	assignRating: vi.fn(),
	getRatingDefinitions: vi.fn()
}));

vi.mock('$lib/stores/auth', () => ({
	authStore: {
		subscribe: vi.fn((callback) => {
			callback({
				user: { id: 'user-1', email: 'admin@example.com', role: 'admin' },
				isAuthenticated: true
			});
			return () => {};
		})
	}
}));

import { getSubmission } from '$lib/api/submissions';
import { getWorkflowHistory, getWorkflowCurrentState, transitionWorkflowState } from '$lib/api/workflow';
import { getSubmissionRatings, getCurrentRating, assignRating, getRatingDefinitions } from '$lib/api/ratings';
import SubmissionDetailPage from '../[id]/+page.svelte';

// Mock data
const mockSubmission: Submission = {
	id: 'sub-123',
	content: 'https://www.snapchat.com/spotlight/test-video',
	submission_type: 'spotlight',
	status: 'processing',
	user_id: 'user-1',
	created_at: '2025-01-15T10:00:00Z',
	updated_at: '2025-01-15T14:00:00Z',
	user: { id: 'user-1', email: 'submitter@example.com' },
	spotlight_content: {
		spotlight_id: 'spot-123',
		thumbnail_url: 'https://example.com/thumb.jpg',
		creator_name: 'Test Creator',
		creator_username: 'testcreator',
		view_count: 10000,
		duration_ms: 30000
	},
	reviewers: [{ id: 'reviewer-1', email: 'reviewer@example.com' }]
};

const mockWorkflowHistory: WorkflowHistoryResponse = {
	items: [
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
			to_state: 'in_research',
			transitioned_by_id: 'reviewer-1',
			transitioned_by: { id: 'reviewer-1', email: 'reviewer@example.com' },
			reason: 'Starting research',
			metadata: null,
			created_at: '2025-01-15T11:00:00Z'
		}
	],
	total: 2,
	current_state: 'in_research'
};

const mockWorkflowCurrentState: WorkflowCurrentStateResponse = {
	submission_id: 'sub-123',
	current_state: 'in_research',
	valid_transitions: ['draft_ready', 'needs_more_research', 'rejected']
};

const mockRatings: FactCheckRating[] = [
	{
		id: 'rating-1',
		fact_check_id: 'fc-123',
		rating: 'partly_false',
		justification: 'The claim contains some inaccuracies about the date of the event.',
		assigned_by_id: 'reviewer-1',
		version: 1,
		is_current: true,
		created_at: '2025-01-15T12:00:00Z'
	}
];

const mockCurrentRating = {
	rating: mockRatings[0],
	definition: {
		id: 'def-1',
		rating: 'partly_false' as const,
		name: { en: 'Partly False', nl: 'Gedeeltelijk Onjuist' },
		description: { en: 'The claim contains a mix of accurate and inaccurate information.', nl: 'De bewering bevat een mix van juiste en onjuiste informatie.' },
		color_hex: '#FFA500',
		icon: 'alert-triangle',
		display_order: 2,
		created_at: '2025-01-01T00:00:00Z',
		updated_at: '2025-01-01T00:00:00Z'
	}
};

const mockRatingDefinitions = {
	items: [
		{
			id: 'def-1',
			rating: 'true' as const,
			name: { en: 'True', nl: 'Waar' },
			description: { en: 'The claim is accurate.', nl: 'De bewering is juist.' },
			color_hex: '#00FF00',
			icon: 'check',
			display_order: 1,
			created_at: '2025-01-01T00:00:00Z',
			updated_at: '2025-01-01T00:00:00Z'
		},
		{
			id: 'def-2',
			rating: 'false' as const,
			name: { en: 'False', nl: 'Onwaar' },
			description: { en: 'The claim is inaccurate.', nl: 'De bewering is onjuist.' },
			color_hex: '#FF0000',
			icon: 'x',
			display_order: 2,
			created_at: '2025-01-01T00:00:00Z',
			updated_at: '2025-01-01T00:00:00Z'
		}
	],
	total: 2
};

// Create a QueryClient for testing
function createTestQueryClient() {
	return new QueryClient({
		defaultOptions: {
			queries: {
				retry: false,
				staleTime: 0
			}
		}
	});
}

// Helper to render with QueryClient context
function renderWithQueryClient(component: any, props: any) {
	const queryClient = createTestQueryClient();

	return render(component, {
		props,
		context: new Map([['$$_queryClient', queryClient]])
	});
}

describe('SubmissionDetailPage', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();

		// Setup default successful responses
		(getSubmission as Mock).mockResolvedValue(mockSubmission);
		(getWorkflowHistory as Mock).mockResolvedValue(mockWorkflowHistory);
		(getWorkflowCurrentState as Mock).mockResolvedValue(mockWorkflowCurrentState);
		(getSubmissionRatings as Mock).mockResolvedValue(mockRatings);
		(getCurrentRating as Mock).mockResolvedValue(mockCurrentRating);
		(getRatingDefinitions as Mock).mockResolvedValue(mockRatingDefinitions);
	});

	describe('1. Data Display Accuracy', () => {
		it('should display submission content and type correctly', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Snapchat Spotlight/i)).toBeInTheDocument();
			});
		});

		it('should display submitter information', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/submitter@example.com/i)).toBeInTheDocument();
			});
		});

		it('should display creation and update timestamps', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const timeElements = screen.getAllByRole('time');
				expect(timeElements.length).toBeGreaterThan(0);
			});
		});

		it('should display spotlight metadata when available', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Test Creator/i)).toBeInTheDocument();
				expect(screen.getByText(/10,?000/)).toBeInTheDocument();
			});
		});
	});

	describe('2. Component Integration', () => {
		it('should render WorkflowTimeline component with history data', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByRole('list')).toBeInTheDocument();
			});
		});

		it('should render RatingBadge when rating exists', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByRole('status')).toBeInTheDocument();
			});
		});

		it('should display rating justification', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/inaccuracies about the date/i)).toBeInTheDocument();
			});
		});
	});

	describe('3. Permission-Based Visibility', () => {
		it('should show rating assignment form for authorized users', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Assign Rating/i)).toBeInTheDocument();
			});
		});

		it('should show workflow transition controls for admins', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Workflow Transition/i)).toBeInTheDocument();
			});
		});
	});

	describe('4. Form Validation', () => {
		it('should require justification of at least 50 characters for rating', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/Justification/i)).toBeInTheDocument();
			});

			const justificationInput = screen.getByLabelText(/Justification/i);
			const submitBtn = screen.getByRole('button', { name: /Submit Rating/i });

			await fireEvent.input(justificationInput, { target: { value: 'Too short' } });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/50 characters/i)).toBeInTheDocument();
			});
		});

		it('should require selecting a rating before submission', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /Submit Rating/i })).toBeInTheDocument();
			});

			const submitBtn = screen.getByRole('button', { name: /Submit Rating/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(screen.getByText(/select a rating/i)).toBeInTheDocument();
			});
		});

		it('should call API when rating form is valid', async () => {
			(assignRating as Mock).mockResolvedValue({
				id: 'rating-2',
				fact_check_id: 'fc-123',
				rating: 'false',
				justification: 'This is a detailed justification with more than 50 characters explaining why.',
				assigned_by_id: 'admin-1',
				version: 2,
				is_current: true,
				created_at: '2025-01-15T15:00:00Z'
			});

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByLabelText(/Justification/i)).toBeInTheDocument();
			});

			const ratingSelect = screen.getByLabelText(/Rating/i);
			await fireEvent.change(ratingSelect, { target: { value: 'false' } });

			const justificationInput = screen.getByLabelText(/Justification/i);
			await fireEvent.input(justificationInput, {
				target: { value: 'This is a detailed justification with more than 50 characters explaining why.' }
			});

			const submitBtn = screen.getByRole('button', { name: /Submit Rating/i });
			await fireEvent.click(submitBtn);

			await waitFor(() => {
				expect(assignRating).toHaveBeenCalled();
			});
		});
	});

	describe('5. Loading States', () => {
		it('should display loading indicator while fetching data', async () => {
			(getSubmission as Mock).mockImplementation(() => new Promise(() => {}));

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			expect(screen.getByText(/Loading/i)).toBeInTheDocument();
		});
	});

	describe('6. Error States', () => {
		it('should display error message when submission fetch fails', async () => {
			(getSubmission as Mock).mockRejectedValue(new Error('Submission not found'));

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Submission not found/i)).toBeInTheDocument();
			});
		});

		it('should show retry button on error', async () => {
			(getSubmission as Mock).mockRejectedValue(new Error('Network error'));

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
			});
		});
	});

	describe('7. Rating History', () => {
		it('should display rating history with versions', async () => {
			const multipleRatings: FactCheckRating[] = [
				{
					id: 'rating-2',
					fact_check_id: 'fc-123',
					rating: 'false',
					justification: 'Updated rating after additional evidence.',
					assigned_by_id: 'admin-1',
					version: 2,
					is_current: true,
					created_at: '2025-01-15T14:00:00Z'
				},
				{
					id: 'rating-1',
					fact_check_id: 'fc-123',
					rating: 'partly_false',
					justification: 'Initial rating.',
					assigned_by_id: 'reviewer-1',
					version: 1,
					is_current: false,
					created_at: '2025-01-15T12:00:00Z'
				}
			];

			(getSubmissionRatings as Mock).mockResolvedValue(multipleRatings);

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Rating History/i)).toBeInTheDocument();
			});
		});

		it('should display rating timestamps', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const ratingTimeElements = screen.getAllByTestId('rating-timestamp');
				expect(ratingTimeElements.length).toBeGreaterThan(0);
			});
		});
	});

	describe('8. Workflow Transitions', () => {
		it('should display valid transition options', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Draft Ready/i)).toBeInTheDocument();
				expect(screen.getByText(/Needs More Research/i)).toBeInTheDocument();
			});
		});

		it('should open transition modal when clicking transition button', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Draft Ready/i)).toBeInTheDocument();
			});

			const draftReadyBtn = screen.getByText(/Draft Ready/i);
			await fireEvent.click(draftReadyBtn);

			await waitFor(() => {
				expect(screen.getByLabelText(/Transition Reason/i)).toBeInTheDocument();
			});
		});

		it('should call API on workflow transition confirmation', async () => {
			(transitionWorkflowState as Mock).mockResolvedValue({
				id: '3',
				submission_id: 'sub-123',
				from_state: 'in_research',
				to_state: 'draft_ready',
				transitioned_by_id: 'admin-1',
				reason: 'Completed',
				metadata: null,
				created_at: '2025-01-15T15:00:00Z'
			});

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Draft Ready/i)).toBeInTheDocument();
			});

			await fireEvent.click(screen.getByText(/Draft Ready/i));

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /Confirm/i })).toBeInTheDocument();
			});

			const reasonInput = screen.getByLabelText(/Transition Reason/i);
			await fireEvent.input(reasonInput, { target: { value: 'Completed' } });

			await fireEvent.click(screen.getByRole('button', { name: /Confirm/i }));

			await waitFor(() => {
				expect(transitionWorkflowState).toHaveBeenCalled();
			});
		});
	});

	describe('9. Responsive Layout', () => {
		it('should have responsive container classes', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const container = screen.getByTestId('submission-detail-container');
				expect(container.className).toContain('container');
			});
		});

		it('should render grid layout', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const layout = screen.getByTestId('submission-detail-layout');
				expect(layout.className).toContain('grid');
			});
		});
	});

	describe('10. Multilingual Support', () => {
		it('should display content in English by default', async () => {
			locale.set('en');
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Submission Details/i)).toBeInTheDocument();
			});
		});

		it('should display content in Dutch when locale is nl', async () => {
			locale.set('nl');

			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				expect(screen.getByText(/Indiening Details/i)).toBeInTheDocument();
			});
		});
	});

	describe('11. Accessibility', () => {
		it('should have proper heading hierarchy', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const h1 = screen.getByRole('heading', { level: 1 });
				expect(h1).toBeInTheDocument();
			});

			const h2Elements = screen.getAllByRole('heading', { level: 2 });
			expect(h2Elements.length).toBeGreaterThan(0);
		});

		it('should have accessible form labels', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const ratingSelect = screen.getByLabelText(/Rating/i);
				expect(ratingSelect).toBeInTheDocument();

				const justificationInput = screen.getByLabelText(/Justification/i);
				expect(justificationInput).toBeInTheDocument();
			});
		});

		it('should have status role element', async () => {
			renderWithQueryClient(SubmissionDetailPage, { data: { id: 'sub-123' } });

			await waitFor(() => {
				const statusElement = screen.getByRole('status');
				expect(statusElement).toBeInTheDocument();
			});
		});
	});
});
