<script lang="ts">
	import { t } from '$lib/i18n';
	import type { Source, SourceType, SourceRelevance, SourceCreate } from '$lib/api/types';

	interface Props {
		source?: Source;
		mode?: 'add' | 'edit';
		existingSourceCount?: number;
		factCheckId: string;  // Required: fact-check ID for the source
		onSubmit?: (data: SourceCreate) => void | Promise<void>;
		onCancel?: () => void;
	}

	let {
		source,
		mode = 'add',
		existingSourceCount = 0,
		factCheckId,
		onSubmit,
		onCancel
	}: Props = $props();

	// Get today's date in YYYY-MM-DD format
	const getTodayDate = () => new Date().toISOString().split('T')[0];

	// Initialize form state from source prop
	const initialTitle = source?.title ?? '';
	const initialUrl = source?.url ?? '';
	const initialSourceType = source?.source_type ?? '';
	const initialCredibilityScore = source?.credibility_score ?? 0;
	const initialRelevance = source?.relevance ?? '';
	const initialAccessDate = source?.access_date ?? getTodayDate();
	const initialPublicationDate = source?.publication_date ?? '';
	const initialNotes = source?.notes ?? '';

	// Form state
	let title = $state(initialTitle);
	let url = $state(initialUrl);
	let sourceType = $state<SourceType | ''>(initialSourceType);
	let credibilityScore = $state(initialCredibilityScore);
	let relevance = $state<SourceRelevance | ''>(initialRelevance);
	let accessDate = $state(initialAccessDate);
	let publicationDate = $state(initialPublicationDate);
	let notes = $state(initialNotes);
	let isSubmitting = $state(false);

	// Validation errors
	let errors = $state<{
		title?: string;
		url?: string;
		sourceType?: string;
		credibilityScore?: string;
		relevance?: string;
		accessDate?: string;
	}>({});

	// Source type options
	const sourceTypes: SourceType[] = ['primary', 'secondary', 'expert', 'media', 'government', 'academic'];

	// Relevance options
	const relevanceOptions: SourceRelevance[] = ['supports', 'contradicts', 'contextualizes'];

	// Show warning if fewer than 2 sources
	const showWarning = $derived(existingSourceCount < 2);

	function validateForm(): boolean {
		errors = {};
		let isValid = true;

		// Title is required
		if (!title.trim()) {
			errors.title = $t('sources.validation.titleRequired');
			isValid = false;
		}

		// Source type is required
		if (!sourceType) {
			errors.sourceType = $t('sources.validation.typeRequired');
			isValid = false;
		}

		// Access date is required
		if (!accessDate) {
			errors.accessDate = $t('sources.validation.accessDateRequired');
			isValid = false;
		}

		return isValid;
	}

	async function handleSubmit() {
		if (!validateForm()) {
			return;
		}

		isSubmitting = true;

		try {
			const data: SourceCreate = {
				fact_check_id: factCheckId,
				source_type: sourceType as SourceType,
				title: title.trim(),
				access_date: accessDate,
				url: url.trim() || undefined,
				publication_date: publicationDate || undefined,
				credibility_score: credibilityScore || undefined,
				relevance: (relevance as SourceRelevance) || undefined,
				notes: notes.trim() || undefined,
			};

			await onSubmit?.(data);

			// Clear form after successful submission in add mode
			if (mode === 'add') {
				title = '';
				url = '';
				sourceType = '';
				credibilityScore = 0;
				relevance = '';
				accessDate = getTodayDate();
				publicationDate = '';
				notes = '';
			}
		} finally {
			isSubmitting = false;
		}
	}

	function handleStarClick(rating: number) {
		credibilityScore = rating;
	}

	function getStarLabel(index: number): string {
		const count = index + 1;
		if (count === 1) {
			return $t('sources.rating.star', { values: { count } });
		}
		return $t('sources.rating.stars', { values: { count } });
	}
</script>

<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
	<!-- Source count warning -->
	{#if showWarning}
		<div role="alert" class="bg-yellow-50 border border-yellow-200 rounded-md p-3 flex items-start gap-2">
			<svg class="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
			</svg>
			<div class="text-sm">
				<p class="font-medium text-yellow-800">{$t('sources.warning.title')}</p>
				<p class="text-yellow-700">
					{#if existingSourceCount === 1}
						{$t('sources.warning.sourceCount', { values: { count: existingSourceCount } })}
					{:else}
						{$t('sources.warning.sourcesCount', { values: { count: existingSourceCount } })}
					{/if}
				</p>
			</div>
		</div>
	{/if}

	<!-- Title Input (Required) -->
	<div>
		<label for="source-title" class="block text-sm font-medium text-gray-700 mb-1">
			{$t('sources.form.titleLabel')} <span class="text-red-500">*</span>
		</label>
		<input
			id="source-title"
			type="text"
			bind:value={title}
			placeholder={$t('sources.form.titlePlaceholder')}
			class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
			aria-describedby={errors.title ? 'title-error' : undefined}
			required
		/>
		{#if errors.title}
			<p id="title-error" role="alert" class="mt-1 text-sm text-red-600">{errors.title}</p>
		{/if}
	</div>

	<!-- URL Input (Optional) -->
	<div>
		<label for="source-url" class="block text-sm font-medium text-gray-700 mb-1">
			{$t('sources.form.urlLabel')}
		</label>
		<input
			id="source-url"
			type="url"
			bind:value={url}
			placeholder={$t('sources.form.urlPlaceholder')}
			class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
		/>
	</div>

	<!-- Source Type Dropdown -->
	<div>
		<label for="source-type" class="block text-sm font-medium text-gray-700 mb-1">
			{$t('sources.form.typeLabel')} <span class="text-red-500">*</span>
		</label>
		<select
			id="source-type"
			bind:value={sourceType}
			class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
			aria-describedby={errors.sourceType ? 'type-error' : undefined}
			required
		>
			<option value="">{$t('sources.form.typePlaceholder')}</option>
			{#each sourceTypes as type}
				<option value={type}>{$t(`sources.types.${type}`)}</option>
			{/each}
		</select>
		{#if errors.sourceType}
			<p id="type-error" role="alert" class="mt-1 text-sm text-red-600">{errors.sourceType}</p>
		{/if}
	</div>

	<!-- Date Fields -->
	<div class="grid grid-cols-2 gap-4">
		<!-- Access Date (Required) -->
		<div>
			<label for="access-date" class="block text-sm font-medium text-gray-700 mb-1">
				{$t('sources.form.accessDateLabel')} <span class="text-red-500">*</span>
			</label>
			<input
				id="access-date"
				type="date"
				bind:value={accessDate}
				class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
				aria-describedby={errors.accessDate ? 'access-date-error' : undefined}
				required
			/>
			{#if errors.accessDate}
				<p id="access-date-error" role="alert" class="mt-1 text-sm text-red-600">{errors.accessDate}</p>
			{/if}
		</div>

		<!-- Publication Date (Optional) -->
		<div>
			<label for="publication-date" class="block text-sm font-medium text-gray-700 mb-1">
				{$t('sources.form.publicationDateLabel')}
			</label>
			<input
				id="publication-date"
				type="date"
				bind:value={publicationDate}
				class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
			/>
		</div>
	</div>

	<!-- Credibility Score (1-5 stars, optional) -->
	<fieldset aria-labelledby="credibility-legend">
		<legend id="credibility-legend" class="block text-sm font-medium text-gray-700 mb-2">
			{$t('sources.form.credibilityLabel')}
		</legend>
		<div class="flex gap-1">
			{#each [1, 2, 3, 4, 5] as rating, index}
				<button
					type="button"
					onclick={() => handleStarClick(rating)}
					aria-label={getStarLabel(index)}
					aria-pressed={credibilityScore >= rating}
					class="w-8 h-8 flex items-center justify-center text-2xl transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded"
				>
					{#if credibilityScore >= rating}
						<span class="text-yellow-400">★</span>
					{:else}
						<span class="text-gray-300">☆</span>
					{/if}
				</button>
			{/each}
		</div>
	</fieldset>

	<!-- Relevance Selector (Optional) -->
	<div>
		<label for="source-relevance" class="block text-sm font-medium text-gray-700 mb-1">
			{$t('sources.form.relevanceLabel')}
		</label>
		<select
			id="source-relevance"
			bind:value={relevance}
			class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
		>
			<option value="">{$t('sources.form.relevancePlaceholder')}</option>
			{#each relevanceOptions as rel}
				<option value={rel}>{$t(`sources.relevance.${rel}`)}</option>
			{/each}
		</select>
	</div>

	<!-- Notes (Optional) -->
	<div>
		<label for="source-notes" class="block text-sm font-medium text-gray-700 mb-1">
			{$t('sources.form.notesLabel')}
		</label>
		<textarea
			id="source-notes"
			bind:value={notes}
			placeholder={$t('sources.form.notesPlaceholder')}
			rows="3"
			class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
		></textarea>
	</div>

	<!-- Action Buttons -->
	<div class="flex gap-3">
		<button
			type="submit"
			disabled={isSubmitting}
			class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
		>
			{#if isSubmitting}
				{mode === 'edit' ? $t('sources.form.updating') : $t('sources.form.adding')}
			{:else}
				{mode === 'edit' ? $t('sources.form.updateSource') : $t('sources.form.addSource')}
			{/if}
		</button>

		{#if mode === 'edit' && onCancel}
			<button
				type="button"
				onclick={onCancel}
				class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
			>
				{$t('common.cancel')}
			</button>
		{/if}
	</div>
</form>
