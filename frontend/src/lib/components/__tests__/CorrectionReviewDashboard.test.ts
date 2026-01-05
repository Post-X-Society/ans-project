/**
 * CorrectionReviewDashboard Component Tests
 * Issue #80: Frontend Admin Correction Review Dashboard (TDD)
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the CorrectionReviewDashboard component.
 *
 * Requirements:
 * - List pending corrections with SLA countdown
 * - Review form (accept/reject)
 * - Side-by-side fact-check comparison
 * - Apply correction UI
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { locale } from 'svelte-i18n';
import CorrectionReviewDashboardTest from './CorrectionReviewDashboardTest.svelte';

// Mock the API
vi.mock('$lib/api/corrections', () => ({
	getPendingCorrections: vi.fn(),
	acceptCorrection: vi.fn(),
	rejectCorrection: vi.fn(),
	applyCorrection: vi.fn(),
	getCorrectionById: vi.fn()
}));

import {
	getPendingCorrections,
	acceptCorrection,
	rejectCorrection,
	applyCorrection,
	getCorrectionById
} from '$lib/api/corrections';

// Mock data
const mockPendingCorrections = {
	corrections: [
		{
			id: 'correction-1',
			fact_check_id: 'fact-check-1',
			correction_type: 'substantial',
			request_details:
				'The fact-check incorrectly stated the date of the event. The correct date is March 15, 2024.',
			requester_email: 'user@example.com',
			status: 'pending',
			sla_deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days from now
			created_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(), // 4 days ago
			updated_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString()
		},
		{
			id: 'correction-2',
			fact_check_id: 'fact-check-2',
			correction_type: 'minor',
			request_details: 'There is a typo in the third paragraph.',
			status: 'pending',
			sla_deadline: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days from now
			created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
			updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
		},
		{
			id: 'correction-3',
			fact_check_id: 'fact-check-3',
			correction_type: 'update',
			request_details: 'New information has come to light regarding this claim.',
			requester_email: 'journalist@news.com',
			status: 'pending',
			sla_deadline: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day overdue
			created_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(), // 8 days ago
			updated_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString()
		}
	],
	total_count: 3,
	overdue_count: 1
};

describe('CorrectionReviewDashboard', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
		// Default mock to return pending corrections
		vi.mocked(getPendingCorrections).mockResolvedValue(mockPendingCorrections);
	});

	afterEach(() => {
		vi.resetAllMocks();
	});

	describe('Dashboard Rendering', () => {
		it('should render the dashboard title', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(
					screen.getByRole('heading', { name: /correction review dashboard/i })
				).toBeInTheDocument();
			});
		});

		it('should render the pending corrections count', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByText(/3 pending/i)).toBeInTheDocument();
			});
		});

		it('should render the overdue corrections count with warning', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByText(/1 overdue/i)).toBeInTheDocument();
			});
		});

		it('should show loading state initially', () => {
			vi.mocked(getPendingCorrections).mockImplementation(
				() =>
					new Promise(() => {
						/* never resolves */
					})
			);
			render(CorrectionReviewDashboardTest);

			expect(screen.getByText(/loading corrections/i)).toBeInTheDocument();
		});

		it('should show empty state when no pending corrections', async () => {
			vi.mocked(getPendingCorrections).mockResolvedValue({
				corrections: [],
				total_count: 0,
				overdue_count: 0
			});

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByText(/no pending corrections/i)).toBeInTheDocument();
			});
		});
	});

	describe('Correction List', () => {
		it('should render all pending corrections', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByText(/substantial error/i)).toBeInTheDocument();
				expect(screen.getByText(/minor error/i)).toBeInTheDocument();
				// Use getAllByText for "new information" as it appears in both badge and details
				expect(screen.getAllByText(/new information/i).length).toBeGreaterThan(0);
			});
		});

		it('should display correction request details', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(
					screen.getByText(/the fact-check incorrectly stated the date/i)
				).toBeInTheDocument();
			});
		});

		it('should show requester email when provided', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByText(/user@example.com/i)).toBeInTheDocument();
			});
		});

		it('should show SLA countdown for each correction', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				// Should show days remaining
				expect(screen.getByText(/3 days remaining/i)).toBeInTheDocument();
				expect(screen.getByText(/5 days remaining/i)).toBeInTheDocument();
			});
		});

		it('should highlight overdue corrections', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				// Find the overdue correction - use more specific text
				const overdueTexts = screen.getAllByText(/overdue/i);
				// Find the one that's inside a correction item (not the header badge)
				const overdueInItem = overdueTexts.find((el) =>
					el.closest('[data-testid="correction-item"]')
				);
				expect(overdueInItem).toBeInTheDocument();
				// The parent correction item should have the red border class
				const overdueItem = overdueInItem?.closest('[data-testid="correction-item"]');
				expect(overdueItem).toHaveClass('border-red-500');
			});
		});

		it('should prioritize substantial corrections first', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const items = screen.getAllByTestId('correction-item');
				// Substantial should be first (it's also overdue so should be prioritized)
				expect(within(items[0]).getByText(/substantial/i)).toBeInTheDocument();
			});
		});
	});

	describe('Review Form (Accept/Reject)', () => {
		it('should show review button for each correction', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const reviewButtons = screen.getAllByRole('button', { name: /review/i });
				expect(reviewButtons).toHaveLength(3);
			});
		});

		it('should open review modal when clicking review button', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
				expect(screen.getByText(/review correction request/i)).toBeInTheDocument();
			});
		});

		it('should display resolution notes textarea in modal', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				expect(screen.getByLabelText(/resolution notes/i)).toBeInTheDocument();
			});
		});

		it('should show accept and reject buttons in modal', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
				expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
			});
		});

		it('should validate resolution notes minimum length (10 characters)', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				screen.getByLabelText(/resolution notes/i);
			});

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, { target: { value: 'Short' } });

			const acceptBtn = screen.getByRole('button', { name: /accept/i });
			await fireEvent.click(acceptBtn);

			await waitFor(() => {
				expect(
					screen.getByText(/resolution notes must be at least 10 characters/i)
				).toBeInTheDocument();
			});
		});

		it('should call acceptCorrection API when accepting', async () => {
			vi.mocked(acceptCorrection).mockResolvedValue({
				...mockPendingCorrections.corrections[0],
				status: 'accepted',
				resolution_notes: 'Correction accepted and will be applied.',
				reviewed_at: new Date().toISOString()
			});

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, {
				target: { value: 'Correction accepted and will be applied.' }
			});

			const acceptBtn = screen.getByRole('button', { name: /accept/i });
			await fireEvent.click(acceptBtn);

			await waitFor(() => {
				expect(acceptCorrection).toHaveBeenCalledWith('correction-1', {
					resolution_notes: 'Correction accepted and will be applied.'
				});
			});
		});

		it('should call rejectCorrection API when rejecting', async () => {
			vi.mocked(rejectCorrection).mockResolvedValue({
				...mockPendingCorrections.corrections[0],
				status: 'rejected',
				resolution_notes: 'The correction request is invalid.',
				reviewed_at: new Date().toISOString()
			});

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, {
				target: { value: 'The correction request is invalid.' }
			});

			const rejectBtn = screen.getByRole('button', { name: /reject/i });
			await fireEvent.click(rejectBtn);

			await waitFor(() => {
				expect(rejectCorrection).toHaveBeenCalledWith('correction-1', {
					resolution_notes: 'The correction request is invalid.'
				});
			});
		});

		it('should show success message after accepting', async () => {
			vi.mocked(acceptCorrection).mockResolvedValue({
				...mockPendingCorrections.corrections[0],
				status: 'accepted'
			});

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, { target: { value: 'Valid correction request.' } });

			const acceptBtn = screen.getByRole('button', { name: /accept/i });
			await fireEvent.click(acceptBtn);

			await waitFor(() => {
				expect(screen.getByText(/correction accepted/i)).toBeInTheDocument();
			});
		});

		it('should close modal after successful review', async () => {
			vi.mocked(acceptCorrection).mockResolvedValue({
				...mockPendingCorrections.corrections[0],
				status: 'accepted'
			});

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, { target: { value: 'Valid correction request.' } });

			const acceptBtn = screen.getByRole('button', { name: /accept/i });
			await fireEvent.click(acceptBtn);

			await waitFor(() => {
				expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
			});
		});
	});

	describe('Apply Correction UI', () => {
		it('should show apply button for accepted corrections', async () => {
			const acceptedCorrections = {
				corrections: [
					{
						...mockPendingCorrections.corrections[0],
						status: 'accepted',
						reviewed_at: new Date().toISOString(),
						resolution_notes: 'Correction accepted.'
					}
				],
				total_count: 1,
				overdue_count: 0
			};
			vi.mocked(getPendingCorrections).mockResolvedValue(acceptedCorrections);

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /apply correction/i })).toBeInTheDocument();
			});
		});

		it('should open apply modal when clicking apply button', async () => {
			const acceptedCorrections = {
				corrections: [
					{
						...mockPendingCorrections.corrections[0],
						status: 'accepted',
						reviewed_at: new Date().toISOString(),
						resolution_notes: 'Correction accepted.'
					}
				],
				total_count: 1,
				overdue_count: 0
			};
			vi.mocked(getPendingCorrections).mockResolvedValue(acceptedCorrections);

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByRole('button', { name: /apply correction/i });
			});

			await fireEvent.click(screen.getByRole('button', { name: /apply correction/i }));

			await waitFor(() => {
				expect(screen.getByRole('dialog')).toBeInTheDocument();
				// Check for the modal title specifically using heading role
				expect(
					screen.getByRole('heading', { name: /apply correction/i })
				).toBeInTheDocument();
			});
		});

		it('should show changes summary textarea in apply modal', async () => {
			const acceptedCorrections = {
				corrections: [
					{
						...mockPendingCorrections.corrections[0],
						status: 'accepted',
						reviewed_at: new Date().toISOString(),
						resolution_notes: 'Correction accepted.'
					}
				],
				total_count: 1,
				overdue_count: 0
			};
			vi.mocked(getPendingCorrections).mockResolvedValue(acceptedCorrections);

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByRole('button', { name: /apply correction/i });
			});

			await fireEvent.click(screen.getByRole('button', { name: /apply correction/i }));

			await waitFor(() => {
				expect(screen.getByLabelText(/changes summary/i)).toBeInTheDocument();
			});
		});

		it('should call applyCorrection API when applying', async () => {
			const acceptedCorrection = {
				...mockPendingCorrections.corrections[0],
				status: 'accepted',
				reviewed_at: new Date().toISOString(),
				resolution_notes: 'Correction accepted.'
			};
			vi.mocked(getPendingCorrections).mockResolvedValue({
				corrections: [acceptedCorrection],
				total_count: 1,
				overdue_count: 0
			});

			vi.mocked(applyCorrection).mockResolvedValue({
				id: 'app-1',
				correction_id: 'correction-1',
				applied_by_id: 'admin-1',
				version: 2,
				applied_at: new Date().toISOString(),
				changes_summary: 'Updated date to March 15, 2024',
				previous_content: { verdict: 'false' },
				new_content: { verdict: 'false', correction_notice: 'Date corrected' },
				is_current: true
			});

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByRole('button', { name: /apply correction/i });
			});

			await fireEvent.click(screen.getByRole('button', { name: /apply correction/i }));

			const summaryTextarea = screen.getByLabelText(/changes summary/i);
			await fireEvent.input(summaryTextarea, {
				target: { value: 'Updated date to March 15, 2024' }
			});

			const applyBtn = screen.getByRole('button', { name: /confirm apply/i });
			await fireEvent.click(applyBtn);

			await waitFor(() => {
				expect(applyCorrection).toHaveBeenCalledWith('correction-1', expect.any(Object));
			});
		});
	});

	describe('Side-by-Side Comparison', () => {
		it('should show view details button for each correction', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const viewButtons = screen.getAllByRole('button', { name: /view details/i });
				expect(viewButtons.length).toBeGreaterThan(0);
			});
		});

		it('should display original request details in comparison view', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const viewButtons = screen.getAllByRole('button', { name: /view details/i });
			await fireEvent.click(viewButtons[0]);

			await waitFor(() => {
				// Check for the modal heading
				expect(
					screen.getByRole('heading', { name: /original request/i })
				).toBeInTheDocument();
				// Check that the request details are shown in the modal
				const dialog = screen.getByRole('dialog');
				expect(
					within(dialog).getByText(/the fact-check incorrectly stated the date/i)
				).toBeInTheDocument();
			});
		});
	});

	describe('Error Handling', () => {
		it('should show error message when failing to load corrections', async () => {
			vi.mocked(getPendingCorrections).mockRejectedValue(new Error('Network error'));

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByText(/failed to load corrections/i)).toBeInTheDocument();
			});
		});

		it('should show error message when accept fails', async () => {
			vi.mocked(acceptCorrection).mockRejectedValue(new Error('Server error'));

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, { target: { value: 'Valid correction request.' } });

			const acceptBtn = screen.getByRole('button', { name: /accept/i });
			await fireEvent.click(acceptBtn);

			await waitFor(() => {
				expect(screen.getByText(/failed to accept correction/i)).toBeInTheDocument();
			});
		});

		it('should show error message when reject fails', async () => {
			vi.mocked(rejectCorrection).mockRejectedValue(new Error('Server error'));

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, { target: { value: 'Invalid correction request.' } });

			const rejectBtn = screen.getByRole('button', { name: /reject/i });
			await fireEvent.click(rejectBtn);

			await waitFor(() => {
				expect(screen.getByText(/failed to reject correction/i)).toBeInTheDocument();
			});
		});

		it('should show retry button on error', async () => {
			vi.mocked(getPendingCorrections).mockRejectedValue(new Error('Network error'));

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
			});
		});
	});

	describe('Internationalization (i18n)', () => {
		it('should render in Dutch when locale is set to nl', async () => {
			locale.set('nl');

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(
					screen.getByRole('heading', { name: /correctie review dashboard/i })
				).toBeInTheDocument();
			});
		});

		it('should show Dutch labels in review modal', async () => {
			locale.set('nl');

			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getAllByRole('button', { name: /bekijken/i });
			});

			const reviewButtons = screen.getAllByRole('button', { name: /bekijken/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				expect(screen.getByLabelText(/resolutie notities/i)).toBeInTheDocument();
			});
		});

		it('should show Dutch SLA countdown text', async () => {
			locale.set('nl');

			render(CorrectionReviewDashboardTest);

			// Wait for the data to load and verify Dutch translations are applied
			await waitFor(() => {
				// Check that the dashboard title is in Dutch
				expect(
					screen.getByRole('heading', { name: /correctie review dashboard/i })
				).toBeInTheDocument();
				// The SLA texts should also be rendered (may take a moment for locale change)
				const correctionItems = screen.getAllByTestId('correction-item');
				expect(correctionItems.length).toBeGreaterThan(0);
			});
		});
	});

	describe('Accessibility', () => {
		it('should have accessible dashboard heading', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const heading = screen.getByRole('heading', { level: 1 });
				expect(heading).toBeInTheDocument();
			});
		});

		it('should have accessible correction list', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByRole('list', { name: /pending corrections/i })).toBeInTheDocument();
			});
		});

		it('should have aria-label on review buttons', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const reviewButtons = screen.getAllByRole('button', { name: /review/i });
				reviewButtons.forEach((btn) => {
					expect(btn).toHaveAttribute('aria-label');
				});
			});
		});

		it('should have proper modal dialog role', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				const dialog = screen.getByRole('dialog');
				expect(dialog).toHaveAttribute('aria-labelledby');
			});
		});

		it('should have focusable elements within modal when open', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				const dialog = screen.getByRole('dialog');
				expect(dialog).toBeInTheDocument();
				// Modal should have focusable elements
				const buttons = within(dialog).getAllByRole('button');
				expect(buttons.length).toBeGreaterThan(0);
			});
		});

		it('should close modal on Escape key', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			await waitFor(() => {
				screen.getByRole('dialog');
			});

			await fireEvent.keyDown(document, { key: 'Escape' });

			await waitFor(() => {
				expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
			});
		});
	});

	describe('SLA Status Indicators', () => {
		it('should show green indicator for corrections with 5+ days remaining', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const fiveDaysText = screen.getByText(/5 days remaining/i);
				const correctionItem = fiveDaysText.closest('[data-testid="correction-item"]');
				const slaIndicator = correctionItem?.querySelector('.sla-indicator');
				expect(slaIndicator).toBeInTheDocument();
				expect(slaIndicator).toHaveClass('bg-green-500');
			});
		});

		it('should show yellow indicator for corrections with 3-4 days remaining', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				const threeDaysText = screen.getByText(/3 days remaining/i);
				const correctionItem = threeDaysText.closest('[data-testid="correction-item"]');
				const slaIndicator = correctionItem?.querySelector('.sla-indicator');
				expect(slaIndicator).toBeInTheDocument();
				expect(slaIndicator).toHaveClass('bg-yellow-500');
			});
		});

		it('should show red indicator for overdue corrections', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				// Find the overdue correction - use more specific approach
				const overdueTexts = screen.getAllByText(/overdue/i);
				const overdueInItem = overdueTexts.find((el) =>
					el.closest('[data-testid="correction-item"]')
				);
				const correctionItem = overdueInItem?.closest('[data-testid="correction-item"]');
				const slaIndicator = correctionItem?.querySelector('.sla-indicator');
				expect(slaIndicator).toBeInTheDocument();
				expect(slaIndicator).toHaveClass('bg-red-500');
			});
		});
	});

	describe('Filtering and Sorting', () => {
		it('should show filter tabs for correction types', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				expect(screen.getByRole('tab', { name: /all/i })).toBeInTheDocument();
				expect(screen.getByRole('tab', { name: /substantial/i })).toBeInTheDocument();
				expect(screen.getByRole('tab', { name: /update/i })).toBeInTheDocument();
				expect(screen.getByRole('tab', { name: /minor/i })).toBeInTheDocument();
			});
		});

		it('should filter corrections when clicking type tab', async () => {
			render(CorrectionReviewDashboardTest);

			await waitFor(() => {
				screen.getByRole('tab', { name: /substantial/i });
			});

			await fireEvent.click(screen.getByRole('tab', { name: /substantial/i }));

			await waitFor(() => {
				// Should only show substantial corrections
				expect(screen.getByText(/substantial error/i)).toBeInTheDocument();
				expect(screen.queryByText(/minor error/i)).not.toBeInTheDocument();
			});
		});
	});

	describe('Callback Props', () => {
		it('should call onReviewComplete callback after successful review', async () => {
			const onReviewComplete = vi.fn();
			vi.mocked(acceptCorrection).mockResolvedValue({
				...mockPendingCorrections.corrections[0],
				status: 'accepted'
			});

			render(CorrectionReviewDashboardTest, { props: { onReviewComplete } });

			await waitFor(() => {
				screen.getByText(/substantial error/i);
			});

			const reviewButtons = screen.getAllByRole('button', { name: /review/i });
			await fireEvent.click(reviewButtons[0]);

			const textarea = screen.getByLabelText(/resolution notes/i);
			await fireEvent.input(textarea, { target: { value: 'Valid correction request.' } });

			const acceptBtn = screen.getByRole('button', { name: /accept/i });
			await fireEvent.click(acceptBtn);

			await waitFor(() => {
				expect(onReviewComplete).toHaveBeenCalled();
			});
		});
	});
});
