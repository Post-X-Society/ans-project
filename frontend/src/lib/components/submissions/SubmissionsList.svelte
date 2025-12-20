<script lang="ts">
	import { getSubmissions } from '$lib/api/submissions';
	import type { Submission, SubmissionListResponse } from '$lib/api/types';
	import SubmissionCard from './SubmissionCard.svelte';

	interface Props {
		initialData?: SubmissionListResponse;
	}

	let { initialData }: Props = $props();

	// State
	let submissions = $state<Submission[]>(initialData?.items || []);
	let total = $state(initialData?.total || 0);
	let currentPage = $state(initialData?.page || 1);
	let pageSize = $state(initialData?.page_size || 50);
	let totalPages = $state(initialData?.total_pages || 1);
	let isLoading = $state(false);
	let error = $state<string | null>(null);

	// Filter state
	let selectedStatus = $state<'all' | 'pending' | 'processing' | 'completed'>('all');

	/**
	 * Load submissions from API with current filters
	 */
	async function loadSubmissions(page: number = currentPage) {
		isLoading = true;
		error = null;

		try {
			const status = selectedStatus === 'all' ? undefined : selectedStatus;
			const response = await getSubmissions(page, pageSize, status);

			submissions = response.items;
			total = response.total;
			currentPage = response.page;
			pageSize = response.page_size;
			totalPages = response.total_pages;
		} catch (err: any) {
			console.error('Error loading submissions:', err);
			error = err.response?.data?.detail || 'Failed to load submissions';
		} finally {
			isLoading = false;
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
</script>

<div class="space-y-6">
	<!-- Filters Section -->
	<div class="bg-white border border-gray-200 rounded-lg p-4">
		<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
			<div class="flex items-center space-x-4">
				<label for="status-filter" class="text-sm font-medium text-gray-700">
					Filter by status:
				</label>
				<select
					id="status-filter"
					bind:value={selectedStatus}
					onchange={handleStatusChange}
					class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				>
					<option value="all">All Statuses</option>
					<option value="pending">Pending</option>
					<option value="processing">Processing</option>
					<option value="completed">Completed</option>
				</select>
			</div>

			<!-- Results Count -->
			<div class="text-sm text-gray-600">
				Showing {submissions.length} of {total} submission{total !== 1 ? 's' : ''}
			</div>
		</div>
	</div>

	<!-- Loading State -->
	{#if isLoading}
		<div class="text-center py-12">
			<div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"></div>
			<p class="mt-4 text-gray-600">Loading submissions...</p>
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
			<p class="text-red-800 font-medium mb-2">Error Loading Submissions</p>
			<p class="text-red-600 text-sm mb-4">{error}</p>
			<button
				onclick={() => loadSubmissions()}
				class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
			>
				Try Again
			</button>
		</div>

	<!-- Empty State -->
	{:else if submissions.length === 0}
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
			<p class="text-gray-600 font-medium mb-2">No submissions found</p>
			<p class="text-gray-500 text-sm">
				{selectedStatus === 'all'
					? 'No submissions have been created yet.'
					: `No ${selectedStatus} submissions found.`}
			</p>
		</div>

	<!-- Submissions Grid -->
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each submissions as submission (submission.id)}
				<SubmissionCard {submission} />
			{/each}
		</div>

		<!-- Pagination Controls -->
		{#if totalPages > 1}
			<div class="bg-white border border-gray-200 rounded-lg p-4">
				<div class="flex flex-col sm:flex-row items-center justify-between gap-4">
					<!-- Page Info -->
					<div class="text-sm text-gray-600">
						Page {currentPage} of {totalPages}
					</div>

					<!-- Navigation Buttons -->
					<div class="flex items-center space-x-2">
						<button
							onclick={previousPage}
							disabled={currentPage === 1}
							class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
						>
							Previous
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
							Next
						</button>
					</div>
				</div>
			</div>
		{/if}
	{/if}
</div>
