<script lang="ts">
	import { t } from '$lib/i18n';
	import type { Submission } from '$lib/api/types';

	/**
	 * Filter tab identifiers matching URL query parameter values
	 */
	export type FilterTabId = 'all' | 'my-assignments' | 'unassigned' | 'pending-review';

	/**
	 * Workflow states that are considered "pending review" for the current user
	 * Based on ADR 0006: ASSIGNED, IN_RESEARCH, DRAFT_READY, ADMIN_REVIEW, PEER_REVIEW
	 */
	const DEFAULT_PENDING_REVIEW_STATES = [
		'pending',
		'processing',
		'assigned',
		'in_research',
		'draft_ready',
		'admin_review',
		'peer_review'
	];

	interface Props {
		/**
		 * Currently active tab
		 */
		activeTab: FilterTabId;
		/**
		 * List of submissions for calculating badge counts
		 */
		submissions: Submission[];
		/**
		 * Current user ID for filtering "My Assignments"
		 */
		currentUserId: string;
		/**
		 * Workflow states considered as "pending review"
		 */
		pendingReviewStates?: string[];
		/**
		 * Callback when tab changes
		 */
		onTabChange?: (tab: FilterTabId) => void;
	}

	let {
		activeTab,
		submissions,
		currentUserId,
		pendingReviewStates = DEFAULT_PENDING_REVIEW_STATES,
		onTabChange
	}: Props = $props();

	/**
	 * Tab definitions with computed counts
	 */
	const tabs = $derived([
		{
			id: 'all' as FilterTabId,
			labelKey: 'submissions.filterTabs.all',
			count: submissions.length
		},
		{
			id: 'my-assignments' as FilterTabId,
			labelKey: 'submissions.filterTabs.myAssignments',
			count: submissions.filter((s) =>
				s.reviewers.some((r) => r.id === currentUserId)
			).length
		},
		{
			id: 'unassigned' as FilterTabId,
			labelKey: 'submissions.filterTabs.unassigned',
			count: submissions.filter((s) => s.reviewers.length === 0).length
		},
		{
			id: 'pending-review' as FilterTabId,
			labelKey: 'submissions.filterTabs.pendingReview',
			count: submissions.filter(
				(s) =>
					s.reviewers.some((r) => r.id === currentUserId) &&
					pendingReviewStates.includes(s.status)
			).length
		}
	]);

	/**
	 * Handle tab selection via click or keyboard
	 */
	function handleTabClick(tabId: FilterTabId) {
		onTabChange?.(tabId);
	}

	/**
	 * Handle keyboard navigation on tabs
	 */
	function handleKeyDown(event: KeyboardEvent, tabId: FilterTabId) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleTabClick(tabId);
		}
	}

	/**
	 * Get tab button classes based on active state
	 */
	function getTabClasses(isActive: boolean): string {
		const baseClasses =
			'inline-flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2';

		if (isActive) {
			return `${baseClasses} border-primary-600 text-primary-600`;
		}

		return `${baseClasses} border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300`;
	}

	/**
	 * Get badge classes based on active state
	 */
	function getBadgeClasses(isActive: boolean): string {
		const baseClasses = 'inline-flex items-center justify-center min-w-[1.5rem] h-6 px-2 text-xs font-medium rounded-full';

		if (isActive) {
			return `${baseClasses} bg-primary-100 text-primary-700`;
		}

		return `${baseClasses} bg-gray-100 text-gray-600`;
	}
</script>

<div
	role="tablist"
	aria-label={$t('submissions.filterTabs.ariaLabel')}
	class="flex border-b border-gray-200 overflow-x-auto"
>
	{#each tabs as tab (tab.id)}
		{@const isActive = activeTab === tab.id}
		<button
			type="button"
			role="tab"
			id="tab-{tab.id}"
			aria-selected={isActive}
			aria-controls="tabpanel-{tab.id}"
			tabindex={isActive ? 0 : -1}
			class={getTabClasses(isActive)}
			onclick={() => handleTabClick(tab.id)}
			onkeydown={(e) => handleKeyDown(e, tab.id)}
		>
			<span>{$t(tab.labelKey)}</span>
			<span class={getBadgeClasses(isActive)}>
				{tab.count}
			</span>
		</button>
	{/each}
</div>
