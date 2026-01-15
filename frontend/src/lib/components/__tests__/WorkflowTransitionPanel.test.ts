import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale } from 'svelte-i18n';
import WorkflowTransitionPanel from '../WorkflowTransitionPanel.svelte';
import type { WorkflowState, UserRole } from '$lib/api/types';

describe('WorkflowTransitionPanel', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('rendering', () => {
		it('should render the panel with title', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued', 'archived'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByText(/available transitions/i)).toBeInTheDocument();
		});

		it('should have data-testid for testing', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByTestId('workflow-transition-panel')).toBeInTheDocument();
		});

		it('should display the current state badge', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'in_research',
					validTransitions: ['draft_ready'],
					userRole: 'reviewer',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByTestId('workflow-state-badge')).toBeInTheDocument();
		});
	});

	describe('transition buttons', () => {
		it('should render buttons for each valid transition', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued', 'archived', 'rejected'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByRole('button', { name: /queued/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /archived/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /rejected/i })).toBeInTheDocument();
		});

		it('should show no transitions message when validTransitions is empty', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'published',
					validTransitions: [],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByText(/no transitions available/i)).toBeInTheDocument();
		});

		it('should call onTransitionClick when button is clicked', async () => {
			const onTransitionClick = vi.fn();
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick
				}
			});

			const button = screen.getByRole('button', { name: /queued/i });
			await fireEvent.click(button);

			expect(onTransitionClick).toHaveBeenCalledWith('queued');
		});

		it('should call onTransitionClick with correct state for each button', async () => {
			const onTransitionClick = vi.fn();
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'in_research',
					validTransitions: ['draft_ready', 'needs_more_research'],
					userRole: 'reviewer',
					onTransitionClick
				}
			});

			const draftButton = screen.getByRole('button', { name: /draft ready/i });
			await fireEvent.click(draftButton);
			expect(onTransitionClick).toHaveBeenCalledWith('draft_ready');

			const needsMoreButton = screen.getByRole('button', { name: /needs more research/i });
			await fireEvent.click(needsMoreButton);
			expect(onTransitionClick).toHaveBeenCalledWith('needs_more_research');
		});
	});

	describe('loading state', () => {
		it('should disable all buttons when isLoading is true', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued', 'archived'],
					userRole: 'admin',
					onTransitionClick: vi.fn(),
					isLoading: true
				}
			});

			const buttons = screen.getAllByRole('button');
			buttons.forEach((button) => {
				expect(button).toBeDisabled();
			});
		});

		it('should show loading indicator when isLoading is true', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick: vi.fn(),
					isLoading: true
				}
			});

			// Should show loading spinner or indicator
			expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
		});

		it('should not call onTransitionClick when button is clicked and isLoading is true', async () => {
			const onTransitionClick = vi.fn();
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick,
					isLoading: true
				}
			});

			const button = screen.getByRole('button', { name: /queued/i });
			await fireEvent.click(button);

			expect(onTransitionClick).not.toHaveBeenCalled();
		});

		it('should enable buttons when isLoading is false', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued', 'archived'],
					userRole: 'admin',
					onTransitionClick: vi.fn(),
					isLoading: false
				}
			});

			const buttons = screen.getAllByRole('button');
			buttons.forEach((button) => {
				expect(button).not.toBeDisabled();
			});
		});
	});

	describe('button styling per transition type', () => {
		it('should style published transition button as success/green', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'final_approval',
					validTransitions: ['published'],
					userRole: 'super_admin',
					onTransitionClick: vi.fn()
				}
			});

			const button = screen.getByRole('button', { name: /published/i });
			expect(button.className).toContain('bg-emerald');
		});

		it('should style rejected transition button as danger/red', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'admin_review',
					validTransitions: ['rejected'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			const button = screen.getByRole('button', { name: /rejected/i });
			expect(button.className).toContain('bg-red');
		});

		it('should style review transitions as purple', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'draft_ready',
					validTransitions: ['admin_review'],
					userRole: 'reviewer',
					onTransitionClick: vi.fn()
				}
			});

			const button = screen.getByRole('button', { name: /admin review/i });
			expect(button.className).toContain('bg-purple');
		});

		it('should style research transitions as yellow', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'assigned',
					validTransitions: ['in_research'],
					userRole: 'reviewer',
					onTransitionClick: vi.fn()
				}
			});

			const button = screen.getByRole('button', { name: /in research/i });
			expect(button.className).toContain('bg-yellow');
		});
	});

	describe('reason required states', () => {
		it('should show reason required indicator for rejected transition', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'admin_review',
					validTransitions: ['rejected', 'published'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			const rejectedButton = screen.getByRole('button', { name: /rejected/i });
			// Should have some indicator that reason is required
			expect(rejectedButton.textContent).toMatch(/reason required|✱/i);
		});

		it('should show reason required indicator for needs_more_research transition', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'in_research',
					validTransitions: ['needs_more_research', 'draft_ready'],
					userRole: 'reviewer',
					onTransitionClick: vi.fn()
				}
			});

			const needsMoreButton = screen.getByRole('button', { name: /needs more research/i });
			expect(needsMoreButton.textContent).toMatch(/reason required|✱/i);
		});
	});

	describe('accessibility', () => {
		it('should have accessible panel label', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			const panel = screen.getByTestId('workflow-transition-panel');
			expect(panel).toHaveAttribute('role', 'region');
			expect(panel).toHaveAttribute('aria-label');
		});

		it('should have accessible button names', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued', 'archived'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByRole('button', { name: /queued/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /archived/i })).toBeInTheDocument();
		});

		it('should have aria-disabled on buttons when loading', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick: vi.fn(),
					isLoading: true
				}
			});

			const button = screen.getByRole('button', { name: /queued/i });
			expect(button).toBeDisabled();
		});
	});

	describe('multilingual support', () => {
		it('should display English labels', () => {
			locale.set('en');
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'in_research',
					validTransitions: ['draft_ready'],
					userRole: 'reviewer',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByText(/available transitions/i)).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /draft ready/i })).toBeInTheDocument();
		});
	});

	describe('role-based display', () => {
		it('should render for reviewer role', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'assigned',
					validTransitions: ['in_research'],
					userRole: 'reviewer',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByTestId('workflow-transition-panel')).toBeInTheDocument();
		});

		it('should render for admin role', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'admin_review',
					validTransitions: ['peer_review', 'rejected'],
					userRole: 'admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByTestId('workflow-transition-panel')).toBeInTheDocument();
		});

		it('should render for super_admin role', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'final_approval',
					validTransitions: ['published'],
					userRole: 'super_admin',
					onTransitionClick: vi.fn()
				}
			});

			expect(screen.getByTestId('workflow-transition-panel')).toBeInTheDocument();
		});
	});

	describe('error state', () => {
		it('should display error message when error prop is provided', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick: vi.fn(),
					error: 'Failed to transition workflow'
				}
			});

			expect(screen.getByText(/failed to transition workflow/i)).toBeInTheDocument();
		});

		it('should show error with appropriate styling', () => {
			render(WorkflowTransitionPanel, {
				props: {
					currentState: 'submitted',
					validTransitions: ['queued'],
					userRole: 'admin',
					onTransitionClick: vi.fn(),
					error: 'Error occurred'
				}
			});

			const errorElement = screen.getByText(/error occurred/i);
			expect(errorElement.className).toContain('text-red');
		});
	});
});
