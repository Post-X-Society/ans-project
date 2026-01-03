import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { writable } from 'svelte/store';
import AdminDashboard from '../admin/+page.svelte';
import type { Submission } from '$lib/api/types';
import * as authStore from '$lib/stores/auth';

// Mock the auth store
vi.mock('$lib/stores/auth', () => ({
	currentUser: writable(null)
}));

// Mock workflow transition
vi.mock('$lib/api/workflow', () => ({
	transitionWorkflowState: vi.fn()
}));

describe('Admin Dashboard - TDD', () => {
	const mockAdminReviewSubmissions: Submission[] = [
		{
			id: 'sub-1',
			user_id: 'user-1',
			content: 'Claim pending admin review',
			submission_type: 'text',
			status: 'processing',
			workflow_state: 'admin_review',
			created_at: '2026-01-01T10:00:00Z',
			updated_at: '2026-01-02T10:00:00Z',
			reviewers: [{ id: 'reviewer-1', email: 'reviewer@example.com' }],
			is_assigned_to_me: false,
			user: { id: 'user-1', email: 'submitter1@example.com' }
		},
		{
			id: 'sub-2',
			user_id: 'user-2',
			content: 'Another claim for admin review',
			submission_type: 'text',
			status: 'processing',
			workflow_state: 'admin_review',
			created_at: '2026-01-02T10:00:00Z',
			updated_at: '2026-01-03T10:00:00Z',
			reviewers: [{ id: 'reviewer-2', email: 'reviewer2@example.com' }],
			is_assigned_to_me: false,
			user: { id: 'user-2', email: 'submitter2@example.com' }
		}
	];

	const mockFinalApprovalSubmissions: Submission[] = [
		{
			id: 'sub-10',
			user_id: 'user-10',
			content: 'Claim awaiting final approval',
			submission_type: 'text',
			status: 'processing',
			workflow_state: 'final_approval',
			created_at: '2025-12-25T10:00:00Z',
			updated_at: '2026-01-01T10:00:00Z',
			reviewers: [{ id: 'reviewer-1', email: 'reviewer@example.com' }],
			is_assigned_to_me: false,
			user: { id: 'user-10', email: 'submitter10@example.com' }
		}
	];

	const mockAllSubmissions: Submission[] = [
		...mockAdminReviewSubmissions,
		...mockFinalApprovalSubmissions,
		{
			id: 'sub-20',
			user_id: 'user-20',
			content: 'Regular submission',
			submission_type: 'text',
			status: 'pending',
			workflow_state: 'submitted',
			created_at: '2026-01-03T10:00:00Z',
			updated_at: '2026-01-03T10:00:00Z',
			reviewers: [],
			is_assigned_to_me: false,
			user: { id: 'user-20', email: 'submitter20@example.com' }
		}
	];

	beforeEach(() => {
		vi.clearAllMocks();
		authStore.currentUser.set({
			id: 'admin-user',
			email: 'admin@example.com',
			role: 'admin'
		});
	});

	describe('Page Structure', () => {
		it('should render page title', () => {
			const data = { submissions: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } };

			render(AdminDashboard, { props: { data } });

			expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
		});

		it('should render Pending Admin Review section', () => {
			const data = { submissions: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } };

			const { container } = render(AdminDashboard, { props: { data } });

			const h2s = container.querySelectorAll('h2');
			const headingTexts = Array.from(h2s).map((h) => h.textContent);
			expect(headingTexts).toContain('Pending Admin Review (0)');
		});

		it('should NOT show Pending Final Approval section for regular admin', () => {
			const data = { submissions: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } };

			const { container } = render(AdminDashboard, { props: { data } });

			const h2s = container.querySelectorAll('h2');
			const headingTexts = Array.from(h2s).map((h) => h.textContent);
			expect(headingTexts.some((t) => t?.includes('Pending Final Approval'))).toBe(false);
		});

		it('should show Pending Final Approval section for super_admin', () => {
			authStore.currentUser.set({
				id: 'super-admin-user',
				email: 'superadmin@example.com',
				role: 'super_admin'
			});

			const data = { submissions: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } };

			const { container } = render(AdminDashboard, { props: { data } });

			const h2s = container.querySelectorAll('h2');
			const headingTexts = Array.from(h2s).map((h) => h.textContent);
			expect(headingTexts.some((t) => t?.includes('Pending Final Approval'))).toBe(true);
		});

		it('should render Reviewer Workload section', () => {
			const data = { submissions: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } };

			const { container } = render(AdminDashboard, { props: { data } });

			const h2s = container.querySelectorAll('h2');
			const headingTexts = Array.from(h2s).map((h) => h.textContent);
			expect(headingTexts).toContain('Reviewer Workload');
		});
	});

	describe('Pending Admin Review Section', () => {
		it('should filter and display submissions in admin_review state', () => {
			const data = {
				submissions: {
					items: mockAllSubmissions,
					total: 4,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			// Should show the 2 admin_review submissions
			expect(screen.getByText('Claim pending admin review')).toBeInTheDocument();
			expect(screen.getByText('Another claim for admin review')).toBeInTheDocument();
			// Should NOT show final_approval or submitted submissions
			expect(screen.queryByText('Claim awaiting final approval')).not.toBeInTheDocument();
			expect(screen.queryByText('Regular submission')).not.toBeInTheDocument();
		});

		it('should display count of pending admin reviews in header', () => {
			const data = {
				submissions: {
					items: mockAdminReviewSubmissions,
					total: 2,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByText(/pending admin review \(2\)/i)).toBeInTheDocument();
		});

		it('should show action buttons for each submission', () => {
			const data = {
				submissions: {
					items: [mockAdminReviewSubmissions[0]],
					total: 1,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /request changes/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
		});

		it('should show empty state when no admin review submissions', () => {
			const data = {
				submissions: {
					items: [],
					total: 0,
					page: 1,
					page_size: 100,
					total_pages: 0
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByText(/no submissions pending admin review/i)).toBeInTheDocument();
		});
	});

	describe('Pending Final Approval Section (Super Admin)', () => {
		beforeEach(() => {
			authStore.currentUser.set({
				id: 'super-admin-user',
				email: 'superadmin@example.com',
				role: 'super_admin'
			});
		});

		it('should filter and display submissions in final_approval state', () => {
			const data = {
				submissions: {
					items: mockAllSubmissions,
					total: 4,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByText('Claim awaiting final approval')).toBeInTheDocument();
		});

		it('should display count of pending final approvals in header', () => {
			const data = {
				submissions: {
					items: mockFinalApprovalSubmissions,
					total: 1,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByText(/pending final approval \(1\)/i)).toBeInTheDocument();
		});

		it('should show Publish and Send Back buttons', () => {
			const data = {
				submissions: {
					items: mockFinalApprovalSubmissions,
					total: 1,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument();
			expect(screen.getByRole('button', { name: /send back/i })).toBeInTheDocument();
		});
	});

	describe('Reviewer Workload Section', () => {
		it('should calculate and display workload per reviewer', () => {
			const data = {
				submissions: {
					items: [
						{
							...mockAdminReviewSubmissions[0],
							reviewers: [
								{ id: 'rev-1', email: 'john@example.com', name: 'John Doe' }
							]
						},
						{
							...mockAdminReviewSubmissions[1],
							reviewers: [
								{ id: 'rev-1', email: 'john@example.com', name: 'John Doe' }
							]
						},
						{
							id: 'sub-3',
							user_id: 'user-3',
							content: 'Third submission',
							submission_type: 'text',
							status: 'processing',
							workflow_state: 'in_research',
							created_at: '2026-01-03T10:00:00Z',
							updated_at: '2026-01-03T10:00:00Z',
							reviewers: [
								{ id: 'rev-2', email: 'mary@example.com', name: 'Mary Smith' }
							],
							is_assigned_to_me: false,
							user: { id: 'user-3', email: 'submitter3@example.com' }
						}
					],
					total: 3,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			const { container } = render(AdminDashboard, { props: { data } });

			// Find the Reviewer Workload section
			const sections = container.querySelectorAll('section');
			const workloadSection = Array.from(sections).find((s) =>
				s.querySelector('h2')?.textContent?.includes('Reviewer Workload')
			);

			expect(workloadSection).toBeInTheDocument();
			expect(workloadSection?.textContent).toContain('John Doe');
			expect(workloadSection?.textContent).toContain('2 pending');
			expect(workloadSection?.textContent).toContain('Mary Smith');
			expect(workloadSection?.textContent).toContain('1 pending');
		});

		it('should show empty state when no reviewers have assignments', () => {
			const data = {
				submissions: {
					items: [],
					total: 0,
					page: 1,
					page_size: 100,
					total_pages: 0
				}
			};

			render(AdminDashboard, { props: { data } });

			expect(screen.getByText(/no reviewer workload data/i)).toBeInTheDocument();
		});
	});

	describe('Action Modals', () => {
		it('should open approve modal when Approve button clicked', async () => {
			const data = {
				submissions: {
					items: [mockAdminReviewSubmissions[0]],
					total: 1,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			const approveButton = screen.getByRole('button', { name: /approve/i });
			await fireEvent.click(approveButton);

			expect(screen.getByText(/approve submission/i)).toBeInTheDocument();
		});

		it('should open request changes modal when Request Changes button clicked', async () => {
			const data = {
				submissions: {
					items: [mockAdminReviewSubmissions[0]],
					total: 1,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			const { container } = render(AdminDashboard, { props: { data } });

			// Click the "Request Changes" button in the submissions section
			const buttons = screen.getAllByRole('button', { name: /request changes/i });
			const requestChangesButton = buttons[0]; // First button in list (not in modal)
			await fireEvent.click(requestChangesButton);

			// Check modal appeared with specific modal content
			expect(screen.getByText('Please explain what changes are needed for this submission.')).toBeInTheDocument();
			// Should require a comment
			expect(screen.getByLabelText(/comment \*/i)).toBeInTheDocument();
		});

		it('should open reject modal when Reject button clicked', async () => {
			const data = {
				submissions: {
					items: [mockAdminReviewSubmissions[0]],
					total: 1,
					page: 1,
					page_size: 100,
					total_pages: 1
				}
			};

			render(AdminDashboard, { props: { data } });

			const rejectButton = screen.getByRole('button', { name: /reject/i });
			await fireEvent.click(rejectButton);

			expect(screen.getByText(/reject submission/i)).toBeInTheDocument();
			// Should require a reason
			expect(screen.getByLabelText(/reason/i)).toBeInTheDocument();
		});
	});

	describe('Accessibility', () => {
		it('should have proper heading hierarchy', () => {
			const data = { submissions: { items: [], total: 0, page: 1, page_size: 100, total_pages: 0 } };

			const { container } = render(AdminDashboard, { props: { data } });

			const h1 = container.querySelector('h1');
			expect(h1).toBeInTheDocument();
			expect(h1).toHaveTextContent('Admin Dashboard');

			const h2s = container.querySelectorAll('h2');
			expect(h2s.length).toBeGreaterThanOrEqual(2); // At least 2 sections for admin
		});
	});
});
