<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { CitationSource } from '$lib/api/types';

	interface Props {
		text: string;
		sources: CitationSource[];
	}

	let { text, sources }: Props = $props();

	// State
	let selectedSource = $state<CitationSource | null>(null);
	let showPopup = $state(false);
	let copiedFormat = $state<'apa' | 'mla' | null>(null);
	let triggerElement = $state<HTMLButtonElement | null>(null);

	// Parse citation patterns: [1], [2], [1,2,3], [1-3]
	interface ParsedSegment {
		type: 'text' | 'citation';
		content: string;
		citationNumbers?: number[];
	}

	const parsedSegments = $derived.by(() => {
		if (!text) return [];

		const segments: ParsedSegment[] = [];
		// Match [1], [1,2], [1-3], [1, 2, 3] patterns
		const citationPattern = /\[(\d+(?:\s*[-,]\s*\d+)*)\]/g;
		let lastIndex = 0;
		let match;

		while ((match = citationPattern.exec(text)) !== null) {
			// Add text before citation
			if (match.index > lastIndex) {
				segments.push({
					type: 'text',
					content: text.slice(lastIndex, match.index)
				});
			}

			// Parse citation numbers
			const citationContent = match[1];
			const numbers: number[] = [];

			// Handle ranges like "1-3"
			if (citationContent.includes('-')) {
				const [start, end] = citationContent.split('-').map((n) => parseInt(n.trim()));
				for (let i = start; i <= end; i++) {
					numbers.push(i);
				}
			} else {
				// Handle comma-separated like "1,2,3"
				citationContent.split(',').forEach((n) => {
					const num = parseInt(n.trim());
					if (!isNaN(num)) numbers.push(num);
				});
			}

			segments.push({
				type: 'citation',
				content: match[0],
				citationNumbers: numbers
			});

			lastIndex = match.index + match[0].length;
		}

		// Add remaining text
		if (lastIndex < text.length) {
			segments.push({
				type: 'text',
				content: text.slice(lastIndex)
			});
		}

		return segments;
	});

	// Get source by 1-based index
	function getSource(index: number): CitationSource | null {
		return sources[index - 1] || null;
	}

	// Check if citation is valid
	function isValidCitation(index: number): boolean {
		return index >= 1 && index <= sources.length;
	}

	// Open citation popup
	function openPopup(source: CitationSource, element: HTMLButtonElement) {
		selectedSource = source;
		triggerElement = element;
		showPopup = true;
		copiedFormat = null;
	}

	// Close popup
	function closePopup() {
		showPopup = false;
		// Return focus to trigger element
		if (triggerElement) {
			triggerElement.focus();
		}
		selectedSource = null;
		triggerElement = null;
	}

	// Handle escape key
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && showPopup) {
			closePopup();
		}
	}

	// Format date for display
	function formatDate(dateString: string | undefined): string {
		if (!dateString) return '';
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('en-US', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		} catch {
			return dateString;
		}
	}

	// Generate APA citation
	function generateAPA(source: CitationSource): string {
		const author = source.author || $t('citations.noAuthor');
		const year = source.publication_date
			? new Date(source.publication_date).getFullYear()
			: 'n.d.';
		const title = source.title || $t('citations.noTitle');
		const publisher = source.publisher || '';
		const url = source.url;

		// APA format: Author, A. A. (Year). Title. Publisher. URL
		let citation = `${author}. (${year}). ${title}.`;
		if (publisher) citation += ` ${publisher}.`;
		citation += ` ${url}`;

		return citation;
	}

	// Generate MLA citation
	function generateMLA(source: CitationSource): string {
		const author = source.author || $t('citations.noAuthor');
		const title = source.title || $t('citations.noTitle');
		const publisher = source.publisher || '';
		const date = source.publication_date
			? formatDate(source.publication_date)
			: '';
		const url = source.url;

		// MLA format: Author. "Title." Publisher, Date. URL
		let citation = `${author}. "${title}."`;
		if (publisher) citation += ` ${publisher},`;
		if (date) citation += ` ${date}.`;
		citation += ` ${url}`;

		return citation;
	}

	// Copy to clipboard
	async function copyToClipboard(format: 'apa' | 'mla') {
		if (!selectedSource) return;

		const citation = format === 'apa' ? generateAPA(selectedSource) : generateMLA(selectedSource);

		try {
			await navigator.clipboard.writeText(citation);
			copiedFormat = format;
			// Reset after 2 seconds
			setTimeout(() => {
				copiedFormat = null;
			}, 2000);
		} catch {
			console.error('Failed to copy to clipboard');
		}
	}

	// Get display title (fallback to URL domain)
	function getDisplayTitle(source: CitationSource): string {
		if (source.title) return source.title;
		try {
			const url = new URL(source.url);
			return url.hostname;
		} catch {
			return source.url;
		}
	}

	// Get relevance color class
	function getRelevanceColorClass(relevance: string): string {
		switch (relevance) {
			case 'supports':
				return 'text-green-700 bg-green-100';
			case 'contradicts':
				return 'text-red-700 bg-red-100';
			case 'contextualizes':
				return 'text-blue-700 bg-blue-100';
			default:
				return 'text-gray-700 bg-gray-100';
		}
	}

	// Truncate URL for display
	function truncateUrl(url: string, maxLength: number = 50): string {
		if (url.length <= maxLength) return url;
		return url.slice(0, maxLength - 3) + '...';
	}

	// Escape HTML to prevent XSS
	function escapeHtml(text: string): string {
		const div = document.createElement('div');
		div.textContent = text;
		return div.innerHTML;
	}
</script>

<svelte:document on:keydown={handleKeydown} />

<span class="citations-container">
	{#each parsedSegments as segment}
		{#if segment.type === 'text'}
			<span>{escapeHtml(segment.content)}</span>
		{:else if segment.citationNumbers}
			{#each segment.citationNumbers as num, i}
				{@const source = getSource(num)}
				{@const isValid = isValidCitation(num)}
				{#if i > 0}
					<span class="text-gray-500">,</span>
				{/if}
				<button
					type="button"
					class="citation-button mx-0.5 px-1 py-0.5 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors"
					class:opacity-50={!isValid}
					class:cursor-not-allowed={!isValid}
					aria-label={$t('citations.ariaLabel', { values: { number: num } })}
					aria-disabled={!isValid}
					onclick={(e) => {
						if (isValid && source) {
							openPopup(source, e.currentTarget);
						}
					}}
				>
					[{num}]
				</button>
			{/each}
		{/if}
	{/each}
</span>

<!-- Citation Popup/Modal -->
{#if showPopup && selectedSource}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 bg-black/50 z-40"
		data-testid="citation-backdrop"
		onclick={closePopup}
		role="presentation"
	></div>

	<!-- Modal -->
	<div
		role="dialog"
		aria-modal="true"
		aria-labelledby="citation-popup-title"
		class="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[80vh] overflow-auto"
	>
		<!-- Header -->
		<div class="flex items-center justify-between p-4 border-b border-gray-200">
			<h2 id="citation-popup-title" class="text-lg font-semibold text-gray-900">
				{$t('citations.popup.title')}
			</h2>
			<button
				type="button"
				class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300"
				aria-label={$t('citations.popup.close')}
				onclick={closePopup}
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Content -->
		<div class="p-4 space-y-4">
			<!-- Title -->
			<div>
				<h3 class="text-xl font-medium text-gray-900">
					{getDisplayTitle(selectedSource)}
				</h3>
			</div>

			<!-- Author -->
			{#if selectedSource.author}
				<div class="flex items-start gap-2">
					<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
						{$t('citations.popup.author')}:
					</span>
					<span class="text-sm text-gray-900">{selectedSource.author}</span>
				</div>
			{/if}

			<!-- Publication Date -->
			{#if selectedSource.publication_date}
				<div class="flex items-start gap-2">
					<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
						{$t('citations.popup.publicationDate')}:
					</span>
					<span class="text-sm text-gray-900">{formatDate(selectedSource.publication_date)}</span>
				</div>
			{/if}

			<!-- Publisher -->
			{#if selectedSource.publisher}
				<div class="flex items-start gap-2">
					<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
						{$t('citations.popup.publisher')}:
					</span>
					<span class="text-sm text-gray-900">{selectedSource.publisher}</span>
				</div>
			{/if}

			<!-- Source Type -->
			<div class="flex items-start gap-2">
				<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
					{$t('citations.popup.sourceType')}:
				</span>
				<span class="text-sm text-gray-900 capitalize">
					{$t(`sources.types.${selectedSource.source_type}`)}
				</span>
			</div>

			<!-- Credibility Rating -->
			<div class="flex items-start gap-2">
				<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
					{$t('citations.popup.credibility')}:
				</span>
				<div class="flex items-center gap-1">
					{#each Array(5) as _, i}
						<svg
							class="w-4 h-4 {i < selectedSource.credibility_rating ? 'text-yellow-400' : 'text-gray-300'}"
							fill="currentColor"
							viewBox="0 0 20 20"
						>
							<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
						</svg>
					{/each}
					<span class="text-sm text-gray-600 ml-1">({selectedSource.credibility_rating}/5)</span>
				</div>
			</div>

			<!-- Relevance -->
			<div class="flex items-start gap-2">
				<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
					{$t('citations.popup.relevance')}:
				</span>
				<span class="text-sm px-2 py-0.5 rounded-full {getRelevanceColorClass(selectedSource.relevance)}">
					{$t(`sources.relevance.${selectedSource.relevance}`)}
				</span>
			</div>

			<!-- URL -->
			<div class="flex items-start gap-2">
				<span class="text-sm font-medium text-gray-500 w-28 shrink-0">
					{$t('citations.popup.viewSource')}:
				</span>
				<a
					href={selectedSource.url}
					target="_blank"
					rel="noopener noreferrer"
					class="text-sm text-blue-600 hover:text-blue-800 hover:underline break-all"
					title={selectedSource.url}
				>
					{truncateUrl(selectedSource.url)}
				</a>
			</div>
		</div>

		<!-- Copy Citation Section -->
		<div class="p-4 border-t border-gray-200 bg-gray-50">
			<h4 class="text-sm font-medium text-gray-700 mb-3">
				{$t('citations.copy.title')}
			</h4>
			<div class="flex gap-2">
				<button
					type="button"
					class="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
					onclick={() => copyToClipboard('apa')}
				>
					{copiedFormat === 'apa' ? $t('citations.copy.copied') : $t('citations.copy.apa')}
				</button>
				<button
					type="button"
					class="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
					onclick={() => copyToClipboard('mla')}
				>
					{copiedFormat === 'mla' ? $t('citations.copy.copied') : $t('citations.copy.mla')}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.citations-container {
		display: inline;
	}

	.citation-button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		text-decoration: underline;
		text-underline-offset: 2px;
	}
</style>
