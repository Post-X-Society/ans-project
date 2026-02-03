<script lang="ts">
	import { t } from '$lib/i18n';
	import type { Source } from '$lib/api/types';

	interface Props {
		source: Source;
		citationNumber?: number;
		onClose: () => void;
		onDelete?: (sourceId: string) => void;
		isDeleting?: boolean;
	}

	let { source, citationNumber, onClose, onDelete, isDeleting = false }: Props = $props();

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

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	function handleDelete() {
		if (onDelete && confirm($t('sources.deleteConfirm'))) {
			onDelete(source.id);
		}
	}
</script>

<!-- Modal Backdrop -->
<div
	class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
	onclick={handleBackdropClick}
	role="presentation"
>
	<!-- Modal Content -->
	<div
		class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
		role="dialog"
		aria-labelledby="modal-title"
		aria-modal="true"
	>
		<!-- Modal Header -->
		<div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-start justify-between">
			<div class="flex items-center gap-3">
				{#if citationNumber}
					<span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-600 text-sm font-semibold">
						{citationNumber}
					</span>
				{/if}
				<h2 id="modal-title" class="text-xl font-semibold text-gray-900">
					{source.title}
				</h2>
			</div>
			<button
				type="button"
				onclick={onClose}
				class="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
				aria-label={$t('common.close')}
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Modal Body -->
		<div class="px-6 py-4 space-y-6">
			<!-- URL -->
			{#if source.url}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.urlLabel')}</h3>
					<a
						href={source.url}
						target="_blank"
						rel="noopener noreferrer"
						class="text-primary-600 hover:text-primary-700 hover:underline break-all block"
					>
						{source.url}
					</a>
				</div>
			{/if}

			<!-- Archived URL -->
			{#if source.archived_url}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.detail.archivedUrl')}</h3>
					<a
						href={source.archived_url}
						target="_blank"
						rel="noopener noreferrer"
						class="text-primary-600 hover:text-primary-700 hover:underline break-all block"
					>
						{source.archived_url}
					</a>
				</div>
			{/if}

			<!-- Metadata Row -->
			<div class="grid grid-cols-2 gap-4">
				<!-- Source Type -->
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.typeLabel')}</h3>
					<span class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-gray-100 text-gray-700">
						{$t(`sources.types.${source.source_type}`)}
					</span>
				</div>

				<!-- Relevance -->
				{#if source.relevance}
					<div>
						<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.relevanceLabel')}</h3>
						<span class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium {getRelevanceBadgeClass(source.relevance)}">
							{$t(`sources.relevance.${source.relevance}`)}
						</span>
					</div>
				{/if}
			</div>

			<!-- Dates -->
			<div class="grid grid-cols-2 gap-4">
				<!-- Access Date -->
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.accessDateLabel')}</h3>
					<p class="text-gray-900">{formatDate(source.access_date)}</p>
				</div>

				<!-- Publication Date -->
				{#if source.publication_date}
					<div>
						<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.publicationDateLabel')}</h3>
						<p class="text-gray-900">{formatDate(source.publication_date)}</p>
					</div>
				{/if}
			</div>

			<!-- Credibility Score -->
			{#if source.credibility_score}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.credibilityLabel')}</h3>
					<div class="flex items-center gap-2">
						<span class="text-2xl text-yellow-400" aria-label="{source.credibility_score}/5 {$t('sources.rating.stars', { values: { count: 5 } })}">
							{renderStars(source.credibility_score)}
						</span>
						<span class="text-sm text-gray-600">({source.credibility_score}/5)</span>
					</div>
				</div>
			{/if}

			<!-- Notes -->
			{#if source.notes}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('sources.form.notesLabel')}</h3>
					<p class="text-gray-900 whitespace-pre-wrap">{source.notes}</p>
				</div>
			{/if}

			<!-- Timestamps -->
			<div class="pt-4 border-t border-gray-200">
				<div class="grid grid-cols-2 gap-4 text-sm text-gray-500">
					<div>
						<span class="font-medium">{$t('sources.detail.createdAt')}:</span>
						<span class="ml-1">{formatDate(source.created_at)}</span>
					</div>
					<div>
						<span class="font-medium">{$t('sources.detail.updatedAt')}:</span>
						<span class="ml-1">{formatDate(source.updated_at)}</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Modal Footer -->
		<div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex items-center justify-between">
			<button
				type="button"
				onclick={onClose}
				class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
			>
				{$t('common.close')}
			</button>

			{#if onDelete}
				<button
					type="button"
					onclick={handleDelete}
					disabled={isDeleting}
					class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
				>
					{#if isDeleting}
						{$t('sources.deleting')}
					{:else}
						{$t('sources.delete')}
					{/if}
				</button>
			{/if}
		</div>
	</div>
</div>
