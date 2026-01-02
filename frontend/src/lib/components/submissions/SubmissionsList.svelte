<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getSubmissions } from '$lib/api/submissions';
	import type { Submission, SubmissionListResponse } from '$lib/api/types';
	import { authStore } from '$lib/stores/auth';
	import { t } from '$lib/i18n';
	import SubmissionCard from './SubmissionCard.svelte';
	import FilterTabs, { type FilterTabId } from './FilterTabs.svelte';

	interface Props {
		initialData?: SubmissionListResponse;
	}

	let { initialData }: Props = $props();

	// Auth state
	let auth = $derived($authStore);
	let currentUserId = $derived(auth.user?.id || '');

	// Check if user has reviewer+ role
	let canViewFilterTabs = $derived(
		auth.user &&
			(auth.user.role === 'reviewer' ||
				auth.user.role === 'admin' ||
				auth.user.role === 'super_admin')
	);

	// State
	let allSubmissions = $state<Submission[]>(initialData?.items || []);
	let total = $state(initialData?.total || 0);
	let currentPage = $state(initialData?.page || 1);
	let pageSize = $state(initialData?.page_size || 50);
	let totalPages = $state(initialData?.total_pages || 1);
	let isLoading = $state(false);
	let error = $state<string | null>(null);

	// Filter states
	let selectedStatus = $state<'all' | 'pending' | 'processing' | 'completed'>('all');

	// Get initial tab from URL or default to 'all'
	function getInitialTab(): FilterTabId {
		if (browser) {
			const urlTab = new URLSearchParams(window.location.search).get('tab');
			if (
				urlTab === 'all' ||
				urlTab === 'my-assignments' ||
				urlTab === 'unassigned' ||
				urlTab === 'pending-review'
			) {
				return urlTab;
			}
		}
		return 'all';
	}

	let activeTab = $state<FilterTabId>(getInitialTab());

	/**
	 * Workflow states considered as "pending review" for current user
	 * Based on ADR 0006: actionable states for reviewers
	 */
	const PENDING_REVIEW_STATES = ['pending', 'processing'];

	/**
	 * Apply client-side filtering based on active tab
	 */
	let filteredSubmissions = $derived.by(() => {
		switch (activeTab) {
			case 'my-assignments':
				return allSubmissions.filter((s) => s.reviewers.some((r) => r.id === currentUserId));
			case 'unassigned':
				return allSubmissions.filter((s) => s.reviewers.length === 0);
			case 'pending-review':
				return allSubmissions.filter(
					(s) =>
						s.reviewers.some((r) => r.id === currentUserId) &&
						PENDING_REVIEW_STATES.includes(s.status)
				);
			case 'all':
			default:
				return allSubmissions;
		}
	});

	/**
	 * Load submissions from API with current filters
	 */
	async function loadSubmissions(page: number = currentPage) {
		isLoading = true;
		error = null;

		try {
			const status = selectedStatus === 'all' ? undefined : selectedStatus;
			// For "my-assignments" tab, use server-side filtering if backend supports it
			const assignedToMe = activeTab === 'my-assignments' ? true : undefined;
			const response = await getSubmissions(page, pageSize, status, assignedToMe);

			allSubmissions = response.items;
			total = response.total;
			currentPage = response.page;
			pageSize = response.page_size;
			totalPages = response.total_pages;
		} catch (err: any) {
			console.error('Error loading submissions:', err);
			error = err.response?.data?.detail || $t('submissions.errorLoadingSubmissions');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Handle tab change with URL persistence
	 */
	function handleTabChange(tab: FilterTabId) {
		activeTab = tab;
		currentPage = 1;

		// Update URL query parameter
		if (browser) {
			const url = new URL(window.location.href);
			if (tab === 'all') {
				url.searchParams.delete('tab');
			} else {
				url.searchParams.set('tab', tab);
			}
			goto(url.pathname + url.search, { replaceState: true, noScroll: true });
		}

		// Reload submissions (server-side filtering for my-assignments)
		if (tab === 'my-assignments' || tab === 'all') {
			loadSubmissions(1);
		}
	}

	/**
	 * Handle status filter change
	 */
	async function handleStatusChange() {
		currentPage = 1; // Reset to first page when filter changes
		await loadSubmissions(1);
	}

	/**
	 * Handle page navigation
	 */
	async function goToPage(page: number) {
		if (page < 1 || page > totalPages || page === currentPage) return;
		await loadSubmissions(page);
	}

	/**
	 * Handle previous page
	 */
	async function previousPage() {
		await goToPage(currentPage - 1);
	}

	/**
	 * Handle next page
	 */
	async function nextPage() {
		await goToPage(currentPage + 1);
	}

	// Sync with URL changes (browser navigation)
	$effect(() => {
		if (browser) {
			const unsubscribe = page.subscribe(($page) => {
				const urlTab = $page.url.searchParams.get('tab') as FilterTabId | null;
				if (
					urlTab &&
					(urlTab === 'all' ||
						urlTab === 'my-assignments' ||
						urlTab === 'unassigned' ||
						urlTab === 'pending-review')
				) {
					if (urlTab !== activeTab) {
						activeTab = urlTab;
					}
				} else if (!urlTab && activeTab !== 'all') {
					activeTab = 'all';
				}
			});
			return unsubscribe;
		}
	});
</script>

<div class="space-y-6">
	<!-- Filter Tabs (only for reviewer+ roles) -->
	{#if canViewFilterTabs}
		<div class="bg-white border border-gray-200 rounded-lg">
			<FilterTabs
				{activeTab}
				submissions={allSubmissions}
				{currentUserId}
				pendingReviewStates={PENDING_REVIEW_STATES}
				onTabChange={handleTabChange}
			/>
		</div>
	{/if}

	<!-- Status Filter Section -->
	<div class="bg-white border border-gray-200 rounded-lg p-4">
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
			<div class="flex items-center space-x-4">
				<label for="status-filter" class="text-sm font-medium text-gray-700">
					{$t('submissions.filterByStatus')}
				</label>
				<select
					id="status-filter"
					bind:value={selectedStatus}
					onchange={handleStatusChange}
					class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				>
					<option value="all">{$t('submissions.allStatuses')}</option>
					<option value="pending">{$t('status.pending')}</option>
					<option value="processing">{$t('status.processing')}</option>
					<option value="completed">{$t('status.completed')}</option>
				</select>
			</div>

			<!-- Results Count -->
			<div class="text-sm text-gray-600">
				{$t('common.showing', {
					values: {
						count: filteredSubmissions.length,
						total: total,
						item: total !== 1 ? 'submissions' : 'submission'
					}
				})}
			</div>
		</div>
	</div>

	<!-- Loading State -->
	{#if isLoading}
		<div class="text-center py-12">
			<div
				class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"
			></div>
			<p class="mt-4 text-gray-600">{$t('submissions.loadingSubmissions')}</p>
		</div>

		<!-- Error State -->
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
			<svg
				class="w-12 h-12 mx-auto text-red-400 mb-3"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<p class="text-red-800 font-medium mb-2">{$t('submissions.errorLoadingSubmissions')}</p>
			<p class="text-red-600 text-sm mb-4">{error}</p>
			<button
				onclick={() => loadSubmissions()}
				class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
			>
				{$t('common.tryAgain')}
			</button>
		</div>

		<!-- Empty State -->
	{:else if filteredSubmissions.length === 0}
		<div class="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
			<svg
				class="w-16 h-16 mx-auto text-gray-400 mb-4"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
				/>
			</svg>
			<p class="text-gray-600 font-medium mb-2">{$t('submissions.noSubmissionsFound')}</p>
			<p class="text-gray-500 text-sm">
				{#if activeTab === 'my-assignments'}
					{$t('submissions.noSubmissionsWithStatus', { values: { status: 'assigned to you' } })}
				{:else if activeTab === 'unassigned'}
					{$t('submissions.noSubmissionsWithStatus', { values: { status: 'unassigned' } })}
				{:else if activeTab === 'pending-review'}
					{$t('submissions.noSubmissionsWithStatus', { values: { status: 'pending review' } })}
				{:else if selectedStatus === 'all'}
					{$t('submissions.noSubmissionsYet')}
				{:else}
					{$t('submissions.noSubmissionsWithStatus', { values: { status: selectedStatus } })}
				{/if}
			</p>
		</div>

		<!-- Submissions Grid -->
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each filteredSubmissions as submission (submission.id)}
				<SubmissionCard {submission} />
			{/each}
		</div>

		<!-- Pagination Controls -->
		{#if totalPages > 1}
			<div class="bg-white border border-gray-200 rounded-lg p-4">
				<div class="flex flex-col sm:flex-row items-center justify-between gap-4">
					<!-- Page Info -->
					<div class="text-sm text-gray-600">
						{$t('common.page', { values: { current: currentPage, total: totalPages } })}
					</div>

					<!-- Navigation Buttons -->
					<div class="flex items-center space-x-2">
						<button
							onclick={previousPage}
							disabled={currentPage === 1}
							class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
						>
							{$t('common.previous')}
						</button>

						<!-- Page Numbers (show current and nearby pages) -->
						<div class="hidden sm:flex items-center space-x-1">
							{#if currentPage > 2}
								<button
									onclick={() => goToPage(1)}
									class="px-3 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
								>
									1
								</button>
								{#if currentPage > 3}
									<span class="px-2 text-gray-400">...</span>
								{/if}
							{/if}

							{#if currentPage > 1}
								<button
									onclick={() => goToPage(currentPage - 1)}
									class="px-3 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
								>
									{currentPage - 1}
								</button>
							{/if}

							<button
								class="px-3 py-2 border-2 border-primary-600 bg-primary-50 rounded text-sm font-medium text-primary-600"
							>
								{currentPage}
							</button>

							{#if currentPage < totalPages}
								<button
									onclick={() => goToPage(currentPage + 1)}
									class="px-3 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
								>
									{currentPage + 1}
								</button>
							{/if}

							{#if currentPage < totalPages - 1}
								{#if currentPage < totalPages - 2}
									<span class="px-2 text-gray-400">...</span>
								{/if}
								<button
									onclick={() => goToPage(totalPages)}
									class="px-3 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
								>
									{totalPages}
								</button>
							{/if}
						</div>

						<button
							onclick={nextPage}
							disabled={currentPage === totalPages}
							class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
						>
							{$t('common.next')}
						</button>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>
