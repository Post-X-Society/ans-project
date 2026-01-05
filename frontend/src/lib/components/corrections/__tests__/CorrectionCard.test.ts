/**
 * CorrectionCard Component Tests
 * Issue #81: Frontend Public Corrections Log Page (TDD)
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the CorrectionCard component
 * for displaying individual corrections in the public corrections log.
 */

import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import CorrectionCardTest from './CorrectionCardTest.svelte';
import type { PublicLogCorrectionResponse } from '$lib/api/types';

describe('CorrectionCard', () => {
	const mockCorrection: PublicLogCorrectionResponse = {
		id: 'correction-123',
		fact_check_id: 'fact-check-456',
		correction_type: 'substantial',
		request_details: 'The rating was incorrect based on new evidence from the primary source.',
		status: 'accepted',
		reviewed_at: '2025-12-20T10:30:00Z',
		resolution_notes: 'Rating updated from false to mostly false based on additional context.',
		created_at: '2025-12-15T08:00:00Z',
		updated_at: '2025-12-20T10:30:00Z'
	};

	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
	});

	describe('Card Rendering', () => {
		it('should render correction type badge', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const badge = container.querySelector('[data-testid="correction-type-badge"]');
			expect(badge).toBeInTheDocument();
			expect(badge).toHaveTextContent(/substantial/i);
		});

		it('should render substantial correction with orange badge', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const badge = container.querySelector('[data-testid="correction-type-badge"]');
			expect(badge).toHaveClass('bg-orange-100', 'text-orange-800');
		});

		it('should render update correction with blue badge', () => {
			const updateCorrection = { ...mockCorrection, correction_type: 'update' as const };
			const { container } = render(CorrectionCardTest, {
				props: { correction: updateCorrection }
			});

			const badge = container.querySelector('[data-testid="correction-type-badge"]');
			expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
		});

		it('should render minor correction with gray badge', () => {
			const minorCorrection = { ...mockCorrection, correction_type: 'minor' as const };
			const { container } = render(CorrectionCardTest, {
				props: { correction: minorCorrection }
			});

			const badge = container.querySelector('[data-testid="correction-type-badge"]');
			expect(badge).toHaveClass('bg-gray-100', 'text-gray-800');
		});

		it('should render correction date', () => {
			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			// The reviewed_at date should be displayed
			expect(screen.getByText(/dec(ember)?\s*20,?\s*2025/i)).toBeInTheDocument();
		});

		it('should render fact-check link', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const link = container.querySelector('a[href*="fact-check-456"]');
			expect(link).toBeInTheDocument();
		});

		it('should render resolution notes/summary of changes', () => {
			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			expect(
				screen.getByText(/rating updated from false to mostly false/i)
			).toBeInTheDocument();
		});

		it('should render accepted status indicator', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const statusBadge = container.querySelector('[data-testid="correction-status-badge"]');
			expect(statusBadge).toBeInTheDocument();
			expect(statusBadge).toHaveTextContent(/accepted/i);
		});
	});

	describe('Correction Details', () => {
		it('should show request details summary', () => {
			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			// Should show at least part of the request details
			expect(screen.getByText(/rating was incorrect/i)).toBeInTheDocument();
		});

		it('should truncate long request details', () => {
			const longDetailsCorrection = {
				...mockCorrection,
				request_details: 'A'.repeat(300)
			};

			render(CorrectionCardTest, {
				props: { correction: longDetailsCorrection }
			});

			// Should show ellipsis or truncated text
			const detailsElement = screen.getByTestId('correction-details');
			expect(detailsElement.textContent?.length).toBeLessThan(300);
		});

		it('should handle missing resolution notes gracefully', () => {
			const noNotesCorrection = {
				...mockCorrection,
				resolution_notes: undefined
			};

			const { container } = render(CorrectionCardTest, {
				props: { correction: noNotesCorrection }
			});

			// Should still render without errors
			expect(container.querySelector('[data-testid="correction-card"]')).toBeInTheDocument();
		});

		it('should handle missing reviewed_at date gracefully', () => {
			const noReviewDateCorrection = {
				...mockCorrection,
				reviewed_at: undefined
			};

			render(CorrectionCardTest, {
				props: { correction: noReviewDateCorrection }
			});

			// Should show created_at date as fallback
			expect(screen.getByText(/dec(ember)?\s*15,?\s*2025/i)).toBeInTheDocument();
		});
	});

	describe('Link Behavior', () => {
		it('should link to fact-check detail page', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const link = container.querySelector('a[data-testid="fact-check-link"]');
			expect(link).toHaveAttribute('href', '/submissions/fact-check-456');
		});

		it('should have accessible link text', () => {
			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const link = screen.getByRole('link', { name: /view (original )?fact-check/i });
			expect(link).toBeInTheDocument();
		});
	});

	describe('Internationalization', () => {
		it('should display Dutch translations when locale is nl', async () => {
			locale.set('nl');

			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			// Wait for locale to update
			await vi.waitFor(() => {
				expect(screen.getByText(/substantieel/i)).toBeInTheDocument();
			});
		});

		it('should display Dutch status when locale is nl', async () => {
			locale.set('nl');

			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			await vi.waitFor(() => {
				expect(screen.getByText(/geaccepteerd/i)).toBeInTheDocument();
			});
		});
	});

	describe('Accessibility', () => {
		it('should have proper heading structure', () => {
			render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			// Card should have a heading for the correction
			expect(screen.getByRole('heading')).toBeInTheDocument();
		});

		it('should have proper time element with datetime attribute', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const timeElement = container.querySelector('time');
			expect(timeElement).toHaveAttribute('datetime');
		});

		it('should have sufficient color contrast for badges', () => {
			const { container } = render(CorrectionCardTest, {
				props: { correction: mockCorrection }
			});

			const badge = container.querySelector('[data-testid="correction-type-badge"]');
			// Orange badge colors should have sufficient contrast
			expect(badge).toHaveClass('bg-orange-100', 'text-orange-800');
		});
	});
});
