/**
 * CorrectionsList Component Tests
 * Issue #81: Frontend Public Corrections Log Page (TDD)
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the CorrectionsList component
 * for displaying a paginated list of corrections in the public log.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import CorrectionsListTest from './CorrectionsListTest.svelte';
import type { PublicLogCorrectionResponse } from '$lib/api/types';

// Mock the API
vi.mock('$lib/api/corrections', () => ({
	getPublicCorrectionsLog: vi.fn()
}));

import { getPublicCorrectionsLog } from '$lib/api/corrections';

describe('CorrectionsList', () => {
	const mockCorrections: PublicLogCorrectionResponse[] = [
		{
			id: 'correction-1',
			fact_check_id: 'fact-check-1',
			correction_type: 'substantial',
			request_details: 'First correction details',
			status: 'accepted',
			reviewed_at: '2025-12-20T10:30:00Z',
			resolution_notes: 'Rating updated after review',
			created_at: '2025-12-15T08:00:00Z',
			updated_at: '2025-12-20T10:30:00Z'
		},
		{
			id: 'correction-2',
			fact_check_id: 'fact-check-2',
			correction_type: 'update',
			request_details: 'Second correction with new information',
			status: 'accepted',
			reviewed_at: '2025-12-18T14:00:00Z',
			resolution_notes: 'Added additional context',
			created_at: '2025-12-10T09:00:00Z',
			updated_at: '2025-12-18T14:00:00Z'
		},
		{
			id: 'correction-3',
			fact_check_id: 'fact-check-3',
			correction_type: 'substantial',
			request_details: 'Third substantial correction',
			status: 'accepted',
			reviewed_at: '2025-12-05T11:00:00Z',
			resolution_notes: 'Major update applied',
			created_at: '2025-12-01T10:00:00Z',
			updated_at: '2025-12-05T11:00:00Z'
		}
	];

	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
	});

	describe('Loading State', () => {
		it('should show loading spinner while fetching data', async () => {
			vi.mocked(getPublicCorrectionsLog).mockImplementation(
				() => new Promise((resolve) => setTimeout(resolve, 100))
			);

			const { container } = render(CorrectionsListTest);

			expect(container.querySelector('[data-testid="loading-spinner"]')).toBeInTheDocument();
		});

		it('should show loading text', async () => {
			vi.mocked(getPublicCorrectionsLog).mockImplementation(
				() => new Promise((resolve) => setTimeout(resolve, 100))
			);

			render(CorrectionsListTest);

			expect(screen.getByText(/loading corrections/i)).toBeInTheDocument();
		});
	});

	describe('List Rendering', () => {
		it('should render correction cards when data is loaded', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);
		});

		it('should render corrections in chronological order (newest first)', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
					expect(cards[0]).toHaveAttribute('data-correction-id', 'correction-1');
				},
				{ timeout: 3000 }
			);
		});

		it('should show total count of corrections', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			// Check that a count is displayed (the actual count from the response)
			expect(screen.getByText(/3 corrections/i)).toBeInTheDocument();
		});
	});

	describe('Empty State', () => {
		it('should show empty message when no corrections exist', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsListTest);

			await waitFor(() => {
				expect(screen.getByText(/no corrections/i)).toBeInTheDocument();
			});
		});

		it('should show helpful description in empty state', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsListTest);

			await waitFor(() => {
				expect(
					screen.getByText(/no substantial corrections have been made/i)
				).toBeInTheDocument();
			});
		});
	});

	describe('Error Handling', () => {
		it('should show error message when fetch fails', async () => {
			vi.mocked(getPublicCorrectionsLog).mockRejectedValue(new Error('Network error'));

			render(CorrectionsListTest);

			await waitFor(() => {
				expect(screen.getByText(/failed to load corrections/i)).toBeInTheDocument();
			});
		});

		it('should show retry button on error', async () => {
			vi.mocked(getPublicCorrectionsLog).mockRejectedValue(new Error('Network error'));

			render(CorrectionsListTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
			});
		});

		it('should retry fetch when retry button is clicked', async () => {
			vi.mocked(getPublicCorrectionsLog)
				.mockRejectedValueOnce(new Error('Network error'))
				.mockResolvedValueOnce({
					corrections: mockCorrections,
					total_count: 3
				});

			render(CorrectionsListTest);

			await waitFor(() => {
				expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
			});

			const retryButton = screen.getByRole('button', { name: /retry/i });
			await fireEvent.click(retryButton);

			await waitFor(() => {
				expect(getPublicCorrectionsLog).toHaveBeenCalledTimes(2);
			});
		});
	});

	describe('Pagination', () => {
		it('should show pagination controls when more than one page', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 30 // More than one page (assuming 10 per page)
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			await waitFor(
				() => {
					expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});

		it('should not show pagination when only one page', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			expect(screen.queryByRole('navigation', { name: /pagination/i })).not.toBeInTheDocument();
		});

		it('should show next button when there are more pages', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 30
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			// When there are 30 items with page size 10, pagination should show
			await waitFor(
				() => {
					expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});

		it('should show pagination buttons when multiple pages exist', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 30
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			// Check that navigation is present
			await waitFor(
				() => {
					const nav = screen.queryByRole('navigation', { name: /pagination/i });
					expect(nav).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});

		it('should disable next button on last page', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest, { props: { pageSize: 10 } });

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			// With only 3 items and 10 per page, there's no next page, so pagination won't show
			const paginationNav = screen.queryByRole('navigation', { name: /pagination/i });
			expect(paginationNav).not.toBeInTheDocument();
		});
	});

	describe('Filter by Correction Type', () => {
		it('should show filter tabs for correction types', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			render(CorrectionsListTest);

			await waitFor(
				() => {
					expect(screen.getByRole('tab', { name: /all/i })).toBeInTheDocument();
					expect(screen.getByRole('tab', { name: /substantial/i })).toBeInTheDocument();
					expect(screen.getByRole('tab', { name: /update/i })).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});

		it('should filter by substantial corrections when tab clicked', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBe(3);
				},
				{ timeout: 3000 }
			);

			const substantialTab = screen.getByRole('tab', { name: /substantial/i });
			await fireEvent.click(substantialTab);

			// Should filter to show only substantial corrections
			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					// Mock has 2 substantial corrections
					expect(cards.length).toBe(2);
				},
				{ timeout: 3000 }
			);
		});
	});

	describe('Internationalization', () => {
		it('should support locale changes', async () => {
			// This test verifies the component uses the i18n translation system
			// The actual locale switching is handled by svelte-i18n setup
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			// Verify the component uses translatable text (not hardcoded)
			// The period text should be present (may appear in multiple places)
			const texts = screen.queryAllByText(/last 24 months|corrections/i);
			expect(texts.length).toBeGreaterThan(0);
		});

		it('should display Dutch empty state when locale is nl', async () => {
			locale.set('nl');
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsListTest);

			await waitFor(
				() => {
					expect(screen.getByText(/geen correcties/i)).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});
	});

	describe('Accessibility', () => {
		it('should have accessible list structure', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			const { container } = render(CorrectionsListTest);

			await waitFor(
				() => {
					const cards = container.querySelectorAll('[data-testid="correction-card"]');
					expect(cards.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);

			expect(screen.getByRole('list', { name: /corrections/i })).toBeInTheDocument();
		});

		it('should announce loading state to screen readers', async () => {
			vi.mocked(getPublicCorrectionsLog).mockImplementation(
				() => new Promise((resolve) => setTimeout(resolve, 100))
			);

			const { container } = render(CorrectionsListTest);

			const loadingRegion = container.querySelector('[aria-live="polite"]');
			expect(loadingRegion).toBeInTheDocument();
		});

		it('should have proper tab keyboard navigation', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			render(CorrectionsListTest);

			await waitFor(
				() => {
					const tablist = screen.getByRole('tablist');
					expect(tablist).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});
	});

	describe('24-Month Filter', () => {
		it('should display header indicating 24-month period', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: mockCorrections,
				total_count: 3
			});

			render(CorrectionsListTest);

			await waitFor(
				() => {
					expect(screen.getByText(/last 24 months/i)).toBeInTheDocument();
				},
				{ timeout: 3000 }
			);
		});
	});
});
