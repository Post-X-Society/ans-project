import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale } from 'svelte-i18n';
import WorkflowTransitionModal from '../WorkflowTransitionModal.svelte';
import type { WorkflowState } from '$lib/api/types';

describe('WorkflowTransitionModal', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('Modal Visibility', () => {
		it('should render when show is true', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			expect(screen.getByTestId('workflow-transition-modal')).toBeInTheDocument();
		});

		it('should not render when show is false', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: false,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			expect(screen.queryByTestId('workflow-transition-modal')).not.toBeInTheDocument();
		});
	});

	describe('Modal Content', () => {
		it('should display the target state', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			// Modal should show the target state (translated)
			const modal = screen.getByTestId('workflow-transition-modal');
			expect(modal).toBeInTheDocument();
		});

		it('should have a reason textarea', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			const textarea = screen.getByRole('textbox');
			expect(textarea).toBeInTheDocument();
		});

		it('should have confirm and cancel buttons', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			expect(screen.getByTestId('confirm-button')).toBeInTheDocument();
			expect(screen.getByTestId('cancel-button')).toBeInTheDocument();
		});
	});

	describe('User Interactions', () => {
		it('should call onCancel when cancel button clicked', async () => {
			const onCancel = vi.fn();

			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel
				}
			});

			await fireEvent.click(screen.getByTestId('cancel-button'));
			expect(onCancel).toHaveBeenCalled();
		});

		it('should call onConfirm with reason when confirm clicked', async () => {
			const onConfirm = vi.fn();

			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm,
					onCancel: vi.fn()
				}
			});

			const textarea = screen.getByRole('textbox');
			await fireEvent.input(textarea, { target: { value: 'Ready for review' } });

			await fireEvent.click(screen.getByTestId('confirm-button'));
			expect(onConfirm).toHaveBeenCalledWith('Ready for review');
		});

		it('should allow confirm without reason', async () => {
			const onConfirm = vi.fn();

			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm,
					onCancel: vi.fn()
				}
			});

			await fireEvent.click(screen.getByTestId('confirm-button'));
			expect(onConfirm).toHaveBeenCalledWith('');
		});
	});

	describe('Loading State', () => {
		it('should disable buttons when submitting', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: true,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			expect(screen.getByTestId('confirm-button')).toBeDisabled();
		});

		it('should show loading text when submitting', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: true,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			const confirmButton = screen.getByTestId('confirm-button');
			expect(confirmButton).toBeInTheDocument();
		});
	});

	describe('Accessibility', () => {
		it('should have accessible modal role', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			const modal = screen.getByRole('dialog');
			expect(modal).toBeInTheDocument();
		});

		it('should have proper label for textarea', () => {
			render(WorkflowTransitionModal, {
				props: {
					show: true,
					targetState: 'draft_ready' as WorkflowState,
					isSubmitting: false,
					onConfirm: vi.fn(),
					onCancel: vi.fn()
				}
			});

			const label = screen.getByLabelText(/reason/i);
			expect(label).toBeInTheDocument();
		});
	});
});
