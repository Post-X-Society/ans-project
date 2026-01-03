import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import TabNavigation from '../TabNavigation.svelte';

describe('TabNavigation', () => {
	const tabs = [
		{ id: 'overview', label: 'Overview' },
		{ id: 'rating', label: 'Rating & Review' },
		{ id: 'sources', label: 'Sources' }
	];

	describe('Rendering', () => {
		it('should render all tabs', () => {
			render(TabNavigation, { props: { tabs, activeTab: 'overview' } });

			expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: 'Rating & Review' })).toBeInTheDocument();
			expect(screen.getByRole('tab', { name: 'Sources' })).toBeInTheDocument();
		});

		it('should mark active tab with aria-selected', () => {
			render(TabNavigation, { props: { tabs, activeTab: 'rating' } });

			const overviewTab = screen.getByRole('tab', { name: 'Overview' });
			const ratingTab = screen.getByRole('tab', { name: 'Rating & Review' });

			expect(overviewTab).toHaveAttribute('aria-selected', 'false');
			expect(ratingTab).toHaveAttribute('aria-selected', 'true');
		});

		it('should apply active styling to selected tab', () => {
			render(TabNavigation, { props: { tabs, activeTab: 'sources' } });

			const sourcesTab = screen.getByRole('tab', { name: 'Sources' });
			expect(sourcesTab.className).toContain('border-primary');
		});
	});

	describe('Tab Switching', () => {
		it('should call onTabChange when tab is clicked', async () => {
			const onTabChange = vi.fn();
			render(TabNavigation, { props: { tabs, activeTab: 'overview', onTabChange } });

			const ratingTab = screen.getByRole('tab', { name: 'Rating & Review' });
			await fireEvent.click(ratingTab);

			expect(onTabChange).toHaveBeenCalledWith('rating');
		});

		it('should not call onTabChange when active tab is clicked', async () => {
			const onTabChange = vi.fn();
			render(TabNavigation, { props: { tabs, activeTab: 'overview', onTabChange } });

			const overviewTab = screen.getByRole('tab', { name: 'Overview' });
			await fireEvent.click(overviewTab);

			expect(onTabChange).not.toHaveBeenCalled();
		});
	});

	describe('Conditional Tabs', () => {
		it('should hide tabs with hidden property', () => {
			const tabsWithHidden = [
				{ id: 'overview', label: 'Overview' },
				{ id: 'peer-reviews', label: 'Peer Reviews', hidden: true }
			];

			render(TabNavigation, { props: { tabs: tabsWithHidden, activeTab: 'overview' } });

			expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
			expect(screen.queryByRole('tab', { name: 'Peer Reviews' })).not.toBeInTheDocument();
		});

		it('should show conditional tabs when hidden is false', () => {
			const tabsWithHidden = [
				{ id: 'overview', label: 'Overview' },
				{ id: 'peer-reviews', label: 'Peer Reviews', hidden: false }
			];

			render(TabNavigation, { props: { tabs: tabsWithHidden, activeTab: 'overview' } });

			expect(screen.getByRole('tab', { name: 'Peer Reviews' })).toBeInTheDocument();
		});
	});

	describe('Accessibility', () => {
		it('should have role="tablist"', () => {
			const { container } = render(TabNavigation, { props: { tabs, activeTab: 'overview' } });

			const tablist = container.querySelector('[role="tablist"]');
			expect(tablist).toBeInTheDocument();
		});

		it('should have role="tab" on each button', () => {
			render(TabNavigation, { props: { tabs, activeTab: 'overview' } });

			const tabButtons = screen.getAllByRole('tab');
			tabButtons.forEach((button) => {
				expect(button).toHaveAttribute('role', 'tab');
			});
		});

		it('should support keyboard navigation', async () => {
			const onTabChange = vi.fn();
			render(TabNavigation, { props: { tabs, activeTab: 'overview', onTabChange } });

			const ratingTab = screen.getByRole('tab', { name: 'Rating & Review' });
			await fireEvent.keyDown(ratingTab, { key: 'Enter' });

			expect(onTabChange).toHaveBeenCalledWith('rating');
		});
	});

	describe('Badge Support', () => {
		it('should display badge count when provided', () => {
			const tabsWithBadge = [
				{ id: 'overview', label: 'Overview' },
				{ id: 'sources', label: 'Sources', badge: 3 }
			];

			render(TabNavigation, { props: { tabs: tabsWithBadge, activeTab: 'overview' } });

			expect(screen.getByText('3')).toBeInTheDocument();
		});

		it('should not display badge when count is 0', () => {
			const tabsWithBadge = [
				{ id: 'sources', label: 'Sources', badge: 0 }
			];

			render(TabNavigation, { props: { tabs: tabsWithBadge, activeTab: 'sources' } });

			const sourcesTab = screen.getByRole('tab', { name: 'Sources' });
			expect(sourcesTab.textContent?.trim()).toBe('Sources');
		});
	});
});
