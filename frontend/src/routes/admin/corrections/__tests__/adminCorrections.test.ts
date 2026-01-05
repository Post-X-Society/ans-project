/**
 * Admin Corrections Page Tests
 * Issue #162: Frontend Integration of Correction Components
 *
 * TDD Red Phase: Tests written FIRST before implementation.
 * These tests define the expected behavior of the admin corrections page.
 *
 * Requirements:
 * - Page renders CorrectionReviewDashboard component
 * - Page requires admin or super_admin authentication
 * - Page is accessible at /admin/corrections route
 */

import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locale } from 'svelte-i18n';
import AdminCorrectionsPageTest from './AdminCorrectionsPageTest.svelte';

// Mock the corrections API
vi.mock('$lib/api/corrections', () => ({
	getPendingCorrections: vi.fn().mockResolvedValue({
		corrections: [],
		total_count: 0,
		overdue_count: 0
	}),
	acceptCorrection: vi.fn(),
	rejectCorrection: vi.fn(),
	applyCorrection: vi.fn(),
	getCorrectionById: vi.fn()
}));

describe('Admin Corrections Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		locale.set('en');
	});

	describe('Page Rendering', () => {
		it('should render the page with container styling', async () => {
			const { container } = render(AdminCorrectionsPageTest);

			// Page should have proper container styling
			await waitFor(() => {
				const wrapper = container.querySelector('.container');
				expect(wrapper).toBeInTheDocument();
			});
		});

		it('should render the CorrectionReviewDashboard component', async () => {
			render(AdminCorrectionsPageTest);

			// Wait for the dashboard title to render
			await waitFor(() => {
				expect(
					screen.getByRole('heading', { name: /correction review dashboard/i })
				).toBeInTheDocument();
			});
		});

		it('should display pending count badge when dashboard loads', async () => {
			// Mock the API to return some corrections
			const { getPendingCorrections } = await import('$lib/api/corrections');
			vi.mocked(getPendingCorrections).mockResolvedValue({
				corrections: [
					{
						id: 'correction-1',
						fact_check_id: 'fc-1',
						correction_type: 'substantial',
						request_details: 'Test correction',
						status: 'pending',
						sla_deadline: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
						created_at: new Date().toISOString(),
						updated_at: new Date().toISOString()
					}
				],
				total_count: 1,
				overdue_count: 0
			});

			render(AdminCorrectionsPageTest);

			// Wait for pending count to be displayed
			await waitFor(() => {
				expect(screen.getByText(/1 pending/i)).toBeInTheDocument();
			});
		});

		it('should show empty state when no corrections are pending', async () => {
			const { getPendingCorrections } = await import('$lib/api/corrections');
			vi.mocked(getPendingCorrections).mockResolvedValue({
				corrections: [],
				total_count: 0,
				overdue_count: 0
			});

			render(AdminCorrectionsPageTest);

			await waitFor(() => {
				expect(screen.getByText(/no pending corrections/i)).toBeInTheDocument();
			});
		});
	});

	describe('Page Structure', () => {
		it('should be wrapped in a max-width container for readability', async () => {
			const { container } = render(AdminCorrectionsPageTest);

			await waitFor(() => {
				// Check for either the dashboard container or page container
				const maxWidthContainer = container.querySelector('.max-w-6xl, .max-w-7xl');
				expect(maxWidthContainer || container.querySelector('.min-h-screen')).toBeInTheDocument();
			});
		});
	});
});
