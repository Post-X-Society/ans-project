import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { locale } from 'svelte-i18n';
import FilterTabs from '../FilterTabs.svelte';
import type { Submission } from '$lib/api/types';

// Mock submissions for testing filter counts
const mockSubmissions: Submission[] = [
	{
		id: '1',
		content: 'Test submission 1',
		submission_type: 'text',
		status: 'pending',
		user_id: 'user-1',
		created_at: '2024-01-01T00:00:00Z',
		updated_at: '2024-01-01T00:00:00Z',
		reviewers: []
	},
	{
		id: '2',
		content: 'Test submission 2',
		submission_type: 'text',
		status: 'processing',
		user_id: 'user-2',
		created_at: '2024-01-02T00:00:00Z',
		updated_at: '2024-01-02T00:00:00Z',
		reviewers: [{ id: 'current-user', email: 'reviewer@test.com' }]
	},
	{
		id: '3',
		content: 'Test submission 3',
		submission_type: 'spotlight',
		status: 'pending',
		user_id: 'user-3',
		created_at: '2024-01-03T00:00:00Z',
		updated_at: '2024-01-03T00:00:00Z',
		reviewers: [
			{ id: 'current-user', email: 'reviewer@test.com' },
			{ id: 'other-user', email: 'other@test.com' }
		]
	},
	{
		id: '4',
		content: 'Test submission 4',
		submission_type: 'url',
		status: 'completed',
		user_id: 'user-4',
		created_at: '2024-01-04T00:00:00Z',
		updated_at: '2024-01-04T00:00:00Z',
		reviewers: [{ id: 'other-user', email: 'other@test.com' }]
	}
];

const currentUserId = 'current-user';

describe('FilterTabs', () => {
	beforeEach(() => {
		locale.set('en');
		vi.clearAllMocks();
	});

	describe('rendering', () => {
		it('should render all four filter tabs', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			expect(screen.getByRole('tab', { name: /all submissions/i })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: /my assignments/i })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: /unassigned/i })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: /pending review/i })).toBeInTheDocument();
		});

		it('should render tablist with correct aria-label', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const tablist = screen.getByRole('tablist');
			expect(tablist).toBeInTheDocument();
			expect(tablist).toHaveAttribute('aria-label', 'Filter submissions');
		});
	});

	describe('active tab state', () => {
		it('should mark "all" tab as selected when activeTab is "all"', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const allTab = screen.getByRole('tab', { name: /all submissions/i });
			expect(allTab).toHaveAttribute('aria-selected', 'true');
		});

		it('should mark "my-assignments" tab as selected when activeTab is "my-assignments"', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'my-assignments',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const myAssignmentsTab = screen.getByRole('tab', { name: /my assignments/i });
			expect(myAssignmentsTab).toHaveAttribute('aria-selected', 'true');
		});

		it('should mark "unassigned" tab as selected when activeTab is "unassigned"', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'unassigned',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const unassignedTab = screen.getByRole('tab', { name: /unassigned/i });
			expect(unassignedTab).toHaveAttribute('aria-selected', 'true');
		});

		it('should mark "pending-review" tab as selected when activeTab is "pending-review"', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'pending-review',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const pendingTab = screen.getByRole('tab', { name: /pending review/i });
			expect(pendingTab).toHaveAttribute('aria-selected', 'true');
		});

		it('should apply active styling to selected tab', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const allTab = screen.getByRole('tab', { name: /all submissions/i });
			// Check for active tab styling classes
			expect(allTab.className).toContain('border-primary-600');
			expect(allTab.className).toContain('text-primary-600');
		});

		it('should apply inactive styling to non-selected tabs', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const myAssignmentsTab = screen.getByRole('tab', { name: /my assignments/i });
			expect(myAssignmentsTab.className).toContain('border-transparent');
			expect(myAssignmentsTab.className).toContain('text-gray-500');
		});
	});

	describe('tab click events', () => {
		it('should fire onTabChange event when clicking a tab', async () => {
			const onTabChange = vi.fn();
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId,
					onTabChange
				}
			});

			const myAssignmentsTab = screen.getByRole('tab', { name: /my assignments/i });
			await fireEvent.click(myAssignmentsTab);

			expect(onTabChange).toHaveBeenCalledWith('my-assignments');
		});

		it('should fire onTabChange with "unassigned" when clicking unassigned tab', async () => {
			const onTabChange = vi.fn();
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId,
					onTabChange
				}
			});

			const unassignedTab = screen.getByRole('tab', { name: /unassigned/i });
			await fireEvent.click(unassignedTab);

			expect(onTabChange).toHaveBeenCalledWith('unassigned');
		});

		it('should fire onTabChange with "pending-review" when clicking pending review tab', async () => {
			const onTabChange = vi.fn();
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId,
					onTabChange
				}
			});

			const pendingTab = screen.getByRole('tab', { name: /pending review/i });
			await fireEvent.click(pendingTab);

			expect(onTabChange).toHaveBeenCalledWith('pending-review');
		});
	});

	describe('badge counters', () => {
		it('should display total count for "all" tab', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const allTab = screen.getByRole('tab', { name: /all submissions/i });
			expect(allTab.textContent).toContain('4');
		});

		it('should display count of submissions assigned to current user for "my assignments" tab', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const myAssignmentsTab = screen.getByRole('tab', { name: /my assignments/i });
			// Submissions 2 and 3 are assigned to current-user
			expect(myAssignmentsTab.textContent).toContain('2');
		});

		it('should display count of unassigned submissions for "unassigned" tab', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const unassignedTab = screen.getByRole('tab', { name: /unassigned/i });
			// Submission 1 has no reviewers
			expect(unassignedTab.textContent).toContain('1');
		});

		it('should display count of pending review submissions for "pending review" tab', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId,
					pendingReviewStates: ['pending', 'processing']
				}
			});

			const pendingTab = screen.getByRole('tab', { name: /pending review/i });
			// Submissions 2 and 3 are assigned to me AND in pending/processing states
			expect(pendingTab.textContent).toContain('2');
		});

		it('should display badge with correct styling', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			// Find badge elements
			const badges = screen.getAllByText(/^\d+$/);
			expect(badges.length).toBeGreaterThan(0);

			// Check that badges have pill-like styling
			badges.forEach((badge) => {
				expect(badge.className).toContain('rounded-full');
			});
		});
	});

	describe('keyboard navigation', () => {
		it('should allow keyboard navigation with Enter key', async () => {
			const onTabChange = vi.fn();
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId,
					onTabChange
				}
			});

			const myAssignmentsTab = screen.getByRole('tab', { name: /my assignments/i });
			myAssignmentsTab.focus();
			await fireEvent.keyDown(myAssignmentsTab, { key: 'Enter' });

			expect(onTabChange).toHaveBeenCalledWith('my-assignments');
		});

		it('should allow keyboard navigation with Space key', async () => {
			const onTabChange = vi.fn();
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId,
					onTabChange
				}
			});

			const unassignedTab = screen.getByRole('tab', { name: /unassigned/i });
			unassignedTab.focus();
			await fireEvent.keyDown(unassignedTab, { key: ' ' });

			expect(onTabChange).toHaveBeenCalledWith('unassigned');
		});
	});

	describe('multilingual support', () => {
		it('should display English labels when locale is en', () => {
			locale.set('en');
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			expect(screen.getByRole('tab', { name: /all submissions/i })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: /my assignments/i })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: /unassigned/i })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: /pending review/i })).toBeInTheDocument();
		});

		it('should update aria-label for tablist based on locale', () => {
			locale.set('en');
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const tablist = screen.getByRole('tablist');
			expect(tablist).toHaveAttribute('aria-label', 'Filter submissions');
		});
	});

	describe('accessibility', () => {
		it('should have proper tablist role', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			expect(screen.getByRole('tablist')).toBeInTheDocument();
		});

		it('should have proper tab roles for all tabs', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const tabs = screen.getAllByRole('tab');
			expect(tabs).toHaveLength(4);
		});

		it('should set tabindex correctly for active and inactive tabs', () => {
			render(FilterTabs, {
				props: {
					activeTab: 'my-assignments',
					submissions: mockSubmissions,
					currentUserId
				}
			});

			const activeTab = screen.getByRole('tab', { name: /my assignments/i });
			expect(activeTab).toHaveAttribute('tabindex', '0');

			const inactiveTab = screen.getByRole('tab', { name: /all submissions/i });
			expect(inactiveTab).toHaveAttribute('tabindex', '-1');
		});
	});

	describe('empty states', () => {
		it('should show 0 for tabs with no matching submissions', () => {
			const emptySubmissions: Submission[] = [];
			render(FilterTabs, {
				props: {
					activeTab: 'all',
					submissions: emptySubmissions,
					currentUserId
				}
			});

			const allTab = screen.getByRole('tab', { name: /all submissions/i });
			expect(allTab.textContent).toContain('0');
		});
	});
});
