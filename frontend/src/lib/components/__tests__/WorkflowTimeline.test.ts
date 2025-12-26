import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale, waitLocale } from 'svelte-i18n';
import WorkflowTimeline from '../WorkflowTimeline.svelte';
import type { WorkflowHistoryItem, WorkflowState } from '$lib/api/types';

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
});
