<script lang="ts">
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import SourceForm from './SourceForm.svelte';
	import SourceDetailModal from './SourceDetailModal.svelte';
	import type { Source, SourceCreate } from '$lib/api/types';
	import { getSources, createSource, deleteSource } from '$lib/api/sources';
	import { t } from '$lib/i18n';

	interface Props {
		factCheckId: string;
	}

	let { factCheckId }: Props = $props();

	let selectedSource = $state<Source | null>(null);
	let selectedSourceCitation = $state<number | undefined>(undefined);

	const queryClient = useQueryClient();

	// Query for sources list
	const sourcesQuery = createQuery(() => ({
		queryKey: ['fact-checks', factCheckId, 'sources'],
		queryFn: () => getSources(factCheckId),
		enabled: !!factCheckId
	}));

	// Mutation for creating source
	const createSourceMutation = createMutation(() => ({
		mutationFn: (data: SourceCreate) => createSource(factCheckId, data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['fact-checks', factCheckId, 'sources'] });
		}
	}));

	// Mutation for deleting source
	const deleteSourceMutation = createMutation(() => ({
		mutationFn: (sourceId: string) => deleteSource(factCheckId, sourceId),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['fact-checks', factCheckId, 'sources'] });
		}
	}));

	let sources = $derived(sourcesQuery.data?.sources ?? []);
	let sourceCount = $derived(sources.length);
	let isLoading = $derived(sourcesQuery.isPending);
	let error = $derived(sourcesQuery.error);

	async function handleSourceSubmit(data: SourceCreate) {
		await createSourceMutation.mutateAsync(data);
	}

	async function handleDelete(sourceId: string) {
		if (confirm($t('sources.deleteConfirm'))) {
			await deleteSourceMutation.mutateAsync(sourceId);
			// Close modal if it's open
			if (selectedSource?.id === sourceId) {
				selectedSource = null;
				selectedSourceCitation = undefined;
			}
		}
	}

	function handleSourceClick(source: Source, index: number) {
		selectedSource = source;
		selectedSourceCitation = index + 1;
	}

	function handleCloseModal() {
		selectedSource = null;
		selectedSourceCitation = undefined;
	}

	function handleDeleteFromModal(sourceId: string) {
		handleDelete(sourceId);
	}

	function getRelevanceBadgeClass(relevance: string): string {
		switch (relevance) {
			case 'supports':
				return 'bg-green-100 text-green-800';
			case 'contradicts':
				return 'bg-red-100 text-red-800';
			case 'contextualizes':
				return 'bg-blue-100 text-blue-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}

	function renderStars(rating: number): string {
		return '★'.repeat(rating) + '☆'.repeat(5 - rating);
	}
</script>

<div class="space-y-6">
	<!-- Source Count Warning -->
	{#if sourceCount < 2}
		<div role="alert" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
			<div class="flex items-start">
				<svg
					class="w-5 h-5 text-yellow-600 mt-0.5 mr-3"
					fill="currentColor"
					viewBox="0 0 20 20"
				>
					<path
						fill-rule="evenodd"
						d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
						clip-rule="evenodd"
					/>
				</svg>
				<div>
					<p class="text-sm font-medium text-yellow-800">
						{$t('sources.warning.title')}
					</p>
					<p class="text-sm text-yellow-700 mt-1">
						{#if sourceCount === 1}
							{$t('sources.warning.sourceCount', { values: { count: sourceCount } })}
						{:else}
							{$t('sources.warning.sourcesCount', { values: { count: sourceCount } })}
						{/if}
					</p>
				</div>
			</div>
		</div>
	{/if}

	<!-- Add Source Form -->
	<div class="bg-white border border-gray-200 rounded-lg p-6">
		<h3 class="text-lg font-semibold text-gray-900 mb-4">{$t('sources.form.addSource')}</h3>
		<SourceForm
			factCheckId={factCheckId}
			onSubmit={handleSourceSubmit}
			existingSourceCount={sourceCount}
		/>
	</div>

	<!-- Sources List -->
	<div class="bg-white border border-gray-200 rounded-lg p-6">
		<h3 class="text-lg font-semibold text-gray-900 mb-4">
			{$t('sources.sourcesList', { values: { count: sourceCount } })}
		</h3>

		{#if isLoading}
			<div class="flex items-center justify-center py-8">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
			</div>
		{:else if error}
			<div role="alert" class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
				{$t('sources.loadError')}
			</div>
		{:else if sources.length === 0}
			<p class="text-gray-500 text-center py-8">{$t('sources.noSources')}</p>
		{:else}
			<div class="space-y-4">
				{#each sources as source, index}
					<div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
						<div class="flex items-start justify-between">
							<button
								type="button"
								onclick={() => handleSourceClick(source, index)}
								class="flex-1 text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded"
							>
								<!-- Source Number and Title -->
								<div class="flex items-center gap-2 mb-2">
									<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-sm font-semibold">
										{index + 1}
									</span>
									<h4 class="font-medium text-gray-900">{source.title}</h4>
								</div>

								<!-- URL if available -->
								{#if source.url}
									<a
										href={source.url}
										target="_blank"
										rel="noopener noreferrer"
										class="text-primary-600 hover:text-primary-700 hover:underline text-sm break-all block mb-2"
									>
										{source.url}
									</a>
								{/if}

								<!-- Metadata -->
								<div class="flex flex-wrap items-center gap-3 mt-2">
									<!-- Source Type -->
									<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
										{$t(`sources.types.${source.source_type}`)}
									</span>

									<!-- Relevance -->
									{#if source.relevance}
										<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium {getRelevanceBadgeClass(source.relevance)}">
											{$t(`sources.relevance.${source.relevance}`)}
										</span>
									{/if}

									<!-- Credibility Rating -->
									{#if source.credibility_score}
										<span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-50 text-yellow-800" title="{source.credibility_score}/5 stars">
											{renderStars(source.credibility_score)}
										</span>
									{/if}
								</div>
							</button>

							<!-- Delete Button -->
							<button
								type="button"
								onclick={() => handleDelete(source.id)}
								disabled={deleteSourceMutation.isPending}
								class="ml-4 p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
								aria-label="{$t('sources.delete')} {index + 1}"
							>
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
									/>
								</svg>
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Source Detail Modal -->
	{#if selectedSource}
		<SourceDetailModal
			source={selectedSource}
			citationNumber={selectedSourceCitation}
			onClose={handleCloseModal}
			onDelete={handleDeleteFromModal}
			isDeleting={deleteSourceMutation.isPending}
		/>
	{/if}
</div>
