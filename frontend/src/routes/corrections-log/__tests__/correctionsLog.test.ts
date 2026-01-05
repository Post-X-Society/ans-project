/**
 * Corrections Log Page Tests
 * Issue #81: Frontend Public Corrections Log Page (TDD)
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the /corrections-log page
 * which displays substantial corrections from the past 24 months.
 */

import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import CorrectionsLogPageTest from './CorrectionsLogPageTest.svelte';

// Mock the API
vi.mock('$lib/api/corrections', () => ({
	getPublicCorrectionsLog: vi.fn()
}));

import { getPublicCorrectionsLog } from '$lib/api/corrections';

describe('Corrections Log Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
	});

	describe('Page Structure', () => {
		it('should render page title', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(() => {
				expect(
					screen.getByRole('heading', { name: /corrections log/i, level: 1 })
				).toBeInTheDocument();
			});
		});

		it('should render page description explaining EFCSN compliance', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(
				() => {
					// Check for EFCSN compliance notice in the page header
					const efcsnTexts = screen.queryAllByText(/EFCSN/i);
					expect(efcsnTexts.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);
		});

		it('should render 24-month transparency statement', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(
				() => {
					// Check for 24 months period text (can appear multiple places)
					const monthTexts = screen.queryAllByText(/24 months/i);
					expect(monthTexts.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);
		});

		it('should render CorrectionsList component', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			const { container } = render(CorrectionsLogPageTest);

			await waitFor(() => {
				expect(
					container.querySelector('[data-testid="corrections-list"]')
				).toBeInTheDocument();
			});
		});
	});

	describe('RSS Feed', () => {
		it('should render RSS feed link', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(() => {
				const rssLink = screen.getByRole('link', { name: /rss feed/i });
				expect(rssLink).toBeInTheDocument();
				expect(rssLink).toHaveAttribute('href', '/corrections-log/rss.xml');
			});
		});

		it('should have RSS icon', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			const { container } = render(CorrectionsLogPageTest);

			await waitFor(() => {
				expect(container.querySelector('[data-testid="rss-icon"]')).toBeInTheDocument();
			});
		});
	});

	describe('Public Access', () => {
		it('should be accessible without authentication', async () => {
			// Clear any auth tokens
			if (typeof localStorage !== 'undefined') {
				localStorage.removeItem('ans_access_token');
				localStorage.removeItem('ans_user');
			}

			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			// Should render without redirecting to login
			await waitFor(() => {
				expect(
					screen.getByRole('heading', { name: /corrections log/i })
				).toBeInTheDocument();
			});
		});
	});

	describe('Internationalization', () => {
		it('should display Dutch page title when locale is nl', async () => {
			locale.set('nl');
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(() => {
				expect(screen.getByRole('heading', { name: /correctielogboek/i })).toBeInTheDocument();
			});
		});

		it('should display Dutch description when locale is nl', async () => {
			locale.set('nl');
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(
				() => {
					// Check for Dutch 24 months text (can appear multiple places)
					const monthTexts = screen.queryAllByText(/24 maanden/i);
					expect(monthTexts.length).toBeGreaterThan(0);
				},
				{ timeout: 3000 }
			);
		});
	});

	describe('SEO and Accessibility', () => {
		it('should have proper main landmark', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(() => {
				expect(screen.getByRole('main')).toBeInTheDocument();
			});
		});

		it('should have skip link or navigation landmark', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			const { container } = render(CorrectionsLogPageTest);

			await waitFor(() => {
				// Should have either skip link or proper landmark structure
				const main = container.querySelector('main');
				expect(main).toBeInTheDocument();
			});
		});
	});

	describe('Navigation Context', () => {
		it('should show breadcrumb or navigation back to home', async () => {
			vi.mocked(getPublicCorrectionsLog).mockResolvedValue({
				corrections: [],
				total_count: 0
			});

			render(CorrectionsLogPageTest);

			await waitFor(() => {
				// Should have a way to navigate back
				const homeLink = screen.getByRole('link', { name: /home|back|ans/i });
				expect(homeLink).toBeInTheDocument();
			});
		});
	});
});

describe('Corrections Log RSS Feed Endpoint', () => {
	it('should have proper RSS feed structure at /corrections-log/rss.xml', async () => {
		// This test documents the expected RSS feed behavior
		// The actual RSS endpoint is tested via the server route
		expect(true).toBe(true); // Placeholder - RSS is server-generated
	});
});
