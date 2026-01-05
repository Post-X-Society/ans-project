<!--
	CorrectionsList Component
	Issue #81: Frontend Public Corrections Log Page (TDD)

	Displays a paginated list of corrections with filtering by type.
	Shows corrections from the past 24 months per EFCSN requirements.
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import { createQuery } from '@tanstack/svelte-query';
	import { publicCorrectionsLogQueryOptions } from '$lib/api/queries';
	import CorrectionCard from './CorrectionCard.svelte';
	import type { CorrectionType, PublicLogCorrectionResponse } from '$lib/api/types';

	interface Props {
		pageSize?: number;
	}

	let { pageSize = 10 }: Props = $props();

	// State
	let currentPage = $state(1);
	let selectedType = $state<CorrectionType | 'all'>('all');

	// Calculate offset based on current page
	const offset = $derived((currentPage - 1) * pageSize);

	// Query for fetching corrections
	const correctionsQuery = createQuery(() =>
		publicCorrectionsLogQueryOptions(pageSize, offset)
	);

	// Access query data directly (TanStack Query v6 with Svelte 5 signals)
	const isLoading = $derived(correctionsQuery.isLoading);
	const isError = $derived(correctionsQuery.isError);
	const data = $derived(correctionsQuery.data);
	const error = $derived(correctionsQuery.error);
	const refetch = correctionsQuery.refetch;

	// Filter corrections by type (client-side)
	const filteredCorrections = $derived.by((): PublicLogCorrectionResponse[] => {
		if (!data?.corrections) return [];
		if (selectedType === 'all') return data.corrections;
		return data.corrections.filter((c) => c.correction_type === selectedType);
	});

	// Pagination calculations
	const totalCount = $derived(data?.total_count || 0);
	const totalPages = $derived(Math.ceil(totalCount / pageSize));
	const hasNextPage = $derived(currentPage < totalPages);
	const hasPreviousPage = $derived(currentPage > 1);

	// Navigation functions
	function goToNextPage() {
		if (hasNextPage) {
			currentPage++;
		}
	}

	function goToPreviousPage() {
		if (hasPreviousPage) {
			currentPage--;
		}
	}

	function handleRetry() {
		refetch();
	}

	function handleTypeFilter(type: CorrectionType | 'all') {
		selectedType = type;
		currentPage = 1; // Reset to first page when filtering
	}

	// Tab configuration
	const filterTabs: Array<{ key: CorrectionType | 'all'; labelKey: string }> = [
		{ key: 'all', labelKey: 'correctionsLog.filters.all' },
		{ key: 'substantial', labelKey: 'correctionsLog.filters.substantial' },
		{ key: 'update', labelKey: 'correctionsLog.filters.update' }
	];
</script>

<div class="space-y-6" data-testid="corrections-list">
	<!-- Header with count and period -->
	<div class="flex items-center justify-between flex-wrap gap-4">
		<p class="text-sm text-gray-600">
			{$t('correctionsLog.list.period', { values: { months: 24 } })}
		</p>
		{#if !isLoading && data}
			<p class="text-sm text-gray-600">
				{$t('correctionsLog.list.totalCount', { values: { count: totalCount } })}
			</p>
		{/if}
	</div>

	<!-- Filter tabs -->
	<div role="tablist" class="flex border-b border-gray-200">
		{#each filterTabs as tab}
			<button
				role="tab"
				aria-selected={selectedType === tab.key}
				class="px-4 py-2 text-sm font-medium border-b-2 transition-colors {selectedType ===
				tab.key
					? 'border-blue-600 text-blue-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				onclick={() => handleTypeFilter(tab.key)}
			>
				{$t(tab.labelKey)}
			</button>
		{/each}
	</div>

	<!-- Loading state -->
	{#if isLoading}
		<div class="flex flex-col items-center justify-center py-12" aria-live="polite">
			<div
				class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
				data-testid="loading-spinner"
			></div>
			<p class="mt-4 text-gray-600">{$t('correctionsLog.list.loading')}</p>
		</div>
	{:else if isError}
		<!-- Error state -->
		<div class="flex flex-col items-center justify-center py-12 text-center">
			<svg
				class="w-12 h-12 text-red-500 mb-4"
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
			<p class="text-gray-900 font-medium mb-2">{$t('correctionsLog.list.errorTitle')}</p>
			<p class="text-gray-600 mb-4">{$t('correctionsLog.list.errorMessage')}</p>
			<button
				onclick={handleRetry}
				class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
			>
				{$t('correctionsLog.list.retry')}
			</button>
		</div>
	{:else if filteredCorrections.length === 0}
		<!-- Empty state -->
		<div class="flex flex-col items-center justify-center py-12 text-center">
			<svg
				class="w-12 h-12 text-gray-400 mb-4"
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
			<p class="text-gray-900 font-medium mb-2">{$t('correctionsLog.list.emptyTitle')}</p>
			<p class="text-gray-600">{$t('correctionsLog.list.emptyMessage')}</p>
		</div>
	{:else}
		<!-- Corrections list -->
		<ul role="list" aria-label={$t('correctionsLog.list.ariaLabel')} class="space-y-4">
			{#each filteredCorrections as correction (correction.id)}
				<li>
					<CorrectionCard {correction} />
				</li>
			{/each}
		</ul>

		<!-- Pagination -->
		{#if totalPages > 1}
			<nav
				role="navigation"
				aria-label={$t('correctionsLog.pagination.ariaLabel')}
				class="flex items-center justify-between border-t border-gray-200 pt-4"
			>
				<div class="flex-1 flex justify-between sm:hidden">
					<button
						onclick={goToPreviousPage}
						disabled={!hasPreviousPage}
						class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{$t('correctionsLog.pagination.previous')}
					</button>
					<button
						onclick={goToNextPage}
						disabled={!hasNextPage}
						class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{$t('correctionsLog.pagination.next')}
					</button>
				</div>
				<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
					<div>
						<p class="text-sm text-gray-700">
							{$t('correctionsLog.pagination.showing', {
								values: {
									start: (currentPage - 1) * pageSize + 1,
									end: Math.min(currentPage * pageSize, totalCount),
									total: totalCount
								}
							})}
						</p>
					</div>
					<div class="flex gap-2">
						<button
							onclick={goToPreviousPage}
							disabled={!hasPreviousPage}
							class="relative inline-flex items-center px-3 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							<span class="sr-only">{$t('correctionsLog.pagination.previous')}</span>
							<svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
								<path
									fill-rule="evenodd"
									d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<span class="text-sm text-gray-700 py-2 px-3">
							{$t('correctionsLog.pagination.page', {
								values: { current: currentPage, total: totalPages }
							})}
						</span>
						<button
							onclick={goToNextPage}
							disabled={!hasNextPage}
							class="relative inline-flex items-center px-3 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							<span class="sr-only">{$t('correctionsLog.pagination.next')}</span>
							<svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
								<path
									fill-rule="evenodd"
									d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					</div>
				</div>
			</nav>
		{/if}
	{/if}
</div>
