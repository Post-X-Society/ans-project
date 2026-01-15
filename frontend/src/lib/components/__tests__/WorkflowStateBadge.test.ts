import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import WorkflowStateBadge from '../WorkflowStateBadge.svelte';
import type { WorkflowState } from '$lib/api/types';

describe('WorkflowStateBadge', () => {
	beforeEach(() => {
		locale.set('en');
	});

	describe('rendering', () => {
		it('should render the badge with correct role and accessible name', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			const badge = screen.getByRole('status');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveAccessibleName(/submitted/i);
		});

		it('should display the state label text', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			expect(screen.getByText(/submitted/i)).toBeInTheDocument();
		});

		it('should have data-testid for testing', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			expect(screen.getByTestId('workflow-state-badge')).toBeInTheDocument();
		});
	});

	describe('color coding per workflow state', () => {
		const stateColors: Array<{
			state: WorkflowState;
			expectedBgClass: string;
			description: string;
		}> = [
			// Initial states - gray
			{ state: 'submitted', expectedBgClass: 'bg-gray-100', description: 'gray for submitted' },
			{ state: 'queued', expectedBgClass: 'bg-blue-100', description: 'blue for queued' },
			{ state: 'archived', expectedBgClass: 'bg-gray-100', description: 'gray for archived' },
			{ state: 'duplicate_detected', expectedBgClass: 'bg-gray-100', description: 'gray for duplicate' },

			// Active workflow states - blue/yellow
			{ state: 'assigned', expectedBgClass: 'bg-blue-100', description: 'blue for assigned' },
			{ state: 'in_research', expectedBgClass: 'bg-yellow-100', description: 'yellow for in_research' },
			{ state: 'draft_ready', expectedBgClass: 'bg-yellow-100', description: 'yellow for draft_ready' },
			{ state: 'needs_more_research', expectedBgClass: 'bg-orange-100', description: 'orange for needs_more_research' },

			// Review states - purple
			{ state: 'admin_review', expectedBgClass: 'bg-purple-100', description: 'purple for admin_review' },
			{ state: 'peer_review', expectedBgClass: 'bg-purple-100', description: 'purple for peer_review' },
			{ state: 'final_approval', expectedBgClass: 'bg-purple-100', description: 'purple for final_approval' },

			// Terminal states
			{ state: 'published', expectedBgClass: 'bg-emerald-100', description: 'emerald for published' },
			{ state: 'rejected', expectedBgClass: 'bg-red-100', description: 'red for rejected' },

			// Correction states
			{ state: 'under_correction', expectedBgClass: 'bg-orange-100', description: 'orange for under_correction' },
			{ state: 'corrected', expectedBgClass: 'bg-emerald-100', description: 'emerald for corrected' }
		];

		stateColors.forEach(({ state, expectedBgClass, description }) => {
			it(`should render ${state} state with ${description}`, () => {
				render(WorkflowStateBadge, { props: { state } });

				const badge = screen.getByRole('status');
				expect(badge.className).toContain(expectedBgClass);
			});
		});
	});

	describe('size variants', () => {
		it('should render small size by default', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-xs');
		});

		it('should render medium size when specified', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted', size: 'md' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-sm');
		});

		it('should render large size when specified', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted', size: 'lg' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('text-base');
		});
	});

	describe('prominent mode', () => {
		it('should render with larger padding when prominent is true', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted', prominent: true } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('px-4');
			expect(badge.className).toContain('py-2');
		});

		it('should render with standard padding by default', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			const badge = screen.getByRole('status');
			expect(badge.className).toContain('px-2');
			expect(badge.className).toContain('py-1');
		});
	});

	describe('multilingual support', () => {
		it('should display English label for submitted state', () => {
			locale.set('en');
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			expect(screen.getByText(/submitted/i)).toBeInTheDocument();
		});

		it('should display English label for in_research state', () => {
			locale.set('en');
			render(WorkflowStateBadge, { props: { state: 'in_research' } });

			expect(screen.getByText(/in research/i)).toBeInTheDocument();
		});

		it('should display English label for admin_review state', () => {
			locale.set('en');
			render(WorkflowStateBadge, { props: { state: 'admin_review' } });

			expect(screen.getByText(/admin review/i)).toBeInTheDocument();
		});

		it('should display English label for published state', () => {
			locale.set('en');
			render(WorkflowStateBadge, { props: { state: 'published' } });

			expect(screen.getByText(/published/i)).toBeInTheDocument();
		});
	});

	describe('accessibility', () => {
		it('should have role="status" for screen readers', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			expect(screen.getByRole('status')).toBeInTheDocument();
		});

		it('should have aria-label describing the workflow state', () => {
			render(WorkflowStateBadge, { props: { state: 'in_research' } });

			const badge = screen.getByRole('status');
			expect(badge).toHaveAttribute('aria-label');
			expect(badge.getAttribute('aria-label')?.toLowerCase()).toContain('in research');
		});

		it('should be focusable when interactive prop is true', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted', interactive: true } });

			const badge = screen.getByRole('status');
			expect(badge).toHaveAttribute('tabindex', '0');
		});

		it('should not be focusable by default', () => {
			render(WorkflowStateBadge, { props: { state: 'submitted' } });

			const badge = screen.getByRole('status');
			expect(badge).not.toHaveAttribute('tabindex');
		});
	});

	describe('icons', () => {
		it('should show icon for published state', () => {
			render(WorkflowStateBadge, { props: { state: 'published' } });

			// Published should show checkmark
			expect(screen.getByText('✓')).toBeInTheDocument();
		});

		it('should show icon for rejected state', () => {
			render(WorkflowStateBadge, { props: { state: 'rejected' } });

			// Rejected should show X
			expect(screen.getByText('✗')).toBeInTheDocument();
		});

		it('should show icon for in_research state', () => {
			render(WorkflowStateBadge, { props: { state: 'in_research' } });

			// In research should show research icon
			expect(screen.getByText('🔍')).toBeInTheDocument();
		});

		it('should show icon for peer_review state', () => {
			render(WorkflowStateBadge, { props: { state: 'peer_review' } });

			// Peer review should show review icon
			expect(screen.getByText('👥')).toBeInTheDocument();
		});
	});
});
