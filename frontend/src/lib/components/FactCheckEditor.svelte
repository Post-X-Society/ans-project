<script lang="ts">
	import { t } from '$lib/i18n';
	import { getDraft, saveDraft } from '$lib/api/drafts';
	import type { DraftResponse, DraftUpdate, FactCheckRatingValue } from '$lib/api/types';

	interface Props {
		factCheckId: string;
		claimText?: string;
		onSubmitForReview?: () => void;
	}

	let { factCheckId, claimText = '', onSubmitForReview }: Props = $props();

	// State
	let isLoading = $state(true);
	let loadError = $state<string | null>(null);
	let isSaving = $state(false);
	let isSubmitting = $state(false);
	let hasUnsavedChanges = $state(false);
	let lastSavedAt = $state<string | null>(null);
	let showPreview = $state(false);
	let successMessage = $state<string | null>(null);
	let validationErrors = $state<Record<string, string>>({});

	// Form data
	let claimSummary = $state('');
	let analysis = $state('');
	let verdict = $state<FactCheckRatingValue | ''>('');
	let justification = $state('');
	let sources = $state<string[]>([]);
	let internalNotes = $state('');

	// Computed values
	let charCount = $derived(analysis.length);
	let wordCount = $derived(analysis.trim() ? analysis.trim().split(/\s+/).length : 0);

	// Auto-save timer
	let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;

	// EFCSN-compliant verdict options
	const verdictOptions: FactCheckRatingValue[] = [
		'true',
		'partly_false',
		'false',
		'missing_context',
		'altered',
		'satire',
		'unverifiable'
	];

	// Load draft on mount
	$effect(() => {
		loadDraft();
		return () => {
			if (autoSaveTimer) {
				clearTimeout(autoSaveTimer);
			}
		};
	});

	async function loadDraft() {
		isLoading = true;
		loadError = null;

		try {
			const response = await getDraft(factCheckId);
			if (response.draft_content) {
				claimSummary = response.draft_content.claim_summary ?? '';
				analysis = response.draft_content.analysis ?? '';
				verdict = response.draft_content.verdict ?? '';
				justification = response.draft_content.justification ?? '';
				sources = response.draft_content.sources_cited ?? [];
				internalNotes = response.draft_content.internal_notes ?? '';
			}
			lastSavedAt = response.draft_updated_at;
		} catch (error) {
			loadError = error instanceof Error ? error.message : $t('factCheckEditor.loadError');
		} finally {
			isLoading = false;
		}
	}

	function handleInputChange() {
		hasUnsavedChanges = true;
		successMessage = null;
		scheduleAutoSave();
	}

	function scheduleAutoSave() {
		if (autoSaveTimer) {
			clearTimeout(autoSaveTimer);
		}
		autoSaveTimer = setTimeout(() => {
			performSave();
		}, 30000);
	}

	function handleBlur() {
		if (hasUnsavedChanges) {
			performSave();
		}
	}

	async function performSave() {
		if (autoSaveTimer) {
			clearTimeout(autoSaveTimer);
			autoSaveTimer = null;
		}

		isSaving = true;

		try {
			const draftData: DraftUpdate = {
				claim_summary: claimSummary || null,
				analysis: analysis || null,
				verdict: verdict || null,
				justification: justification || null,
				sources_cited: sources.filter((s) => s.trim() !== ''),
				internal_notes: internalNotes || null
			};

			const response = await saveDraft(factCheckId, draftData);
			lastSavedAt = response.draft_updated_at;
			hasUnsavedChanges = false;
			successMessage = $t('factCheckEditor.success.saved');

			// Clear success message after 3 seconds
			setTimeout(() => {
				successMessage = null;
			}, 3000);
		} catch (error) {
			console.error('Failed to save draft:', error);
		} finally {
			isSaving = false;
		}
	}

	function validate(): boolean {
		validationErrors = {};

		if (!analysis.trim()) {
			validationErrors['analysis'] = $t('factCheckEditor.validation.analysisRequired');
		} else if (analysis.length < 200) {
			validationErrors['analysis'] = $t('factCheckEditor.validation.analysisMinLength');
		}

		if (!verdict) {
			validationErrors['verdict'] = $t('factCheckEditor.validation.verdictRequired');
		}

		return Object.keys(validationErrors).length === 0;
	}

	async function handleSaveDraft() {
		await performSave();
	}

	async function handleSubmitForReview() {
		if (!validate()) {
			return;
		}

		isSubmitting = true;

		try {
			await performSave();
			if (onSubmitForReview) {
				onSubmitForReview();
			}
			successMessage = $t('factCheckEditor.success.submitted');
		} catch (error) {
			console.error('Failed to submit for review:', error);
		} finally {
			isSubmitting = false;
		}
	}

	function addSource() {
		sources = [...sources, ''];
		handleInputChange();
	}

	function removeSource(index: number) {
		sources = sources.filter((_, i) => i !== index);
		handleInputChange();
	}

	function updateSource(index: number, value: string) {
		sources = sources.map((s, i) => (i === index ? value : s));
		handleInputChange();
	}

	function formatLastSaved(dateString: string | null): string {
		if (!dateString) return '';
		return new Date(dateString).toLocaleTimeString();
	}

	function togglePreview() {
		showPreview = !showPreview;
	}
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="fact-check-editor">
	<!-- Header -->
	<div class="flex items-center justify-between mb-6">
		<h2 class="text-xl font-semibold text-gray-900">{$t('factCheckEditor.title')}</h2>

		<!-- Status Indicator -->
		<div class="flex items-center gap-4">
			{#if isSaving}
				<span class="text-sm text-blue-600 flex items-center gap-1">
					<svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
					</svg>
					{$t('factCheckEditor.status.saving')}
				</span>
			{:else if hasUnsavedChanges}
				<span class="text-sm text-yellow-600">{$t('factCheckEditor.status.unsaved')}</span>
			{:else if lastSavedAt}
				<span class="text-sm text-gray-500">
					{$t('factCheckEditor.status.lastSaved', { values: { time: formatLastSaved(lastSavedAt) } })}
				</span>
			{/if}

			<span class="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700">
				{$t('factCheckEditor.status.draft')}
			</span>
		</div>
	</div>

	<!-- Loading State -->
	{#if isLoading}
		<div class="flex items-center justify-center py-12" role="status">
			<svg class="animate-spin h-8 w-8 text-primary-600 mr-3" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
			</svg>
			<span class="text-lg text-gray-600">{$t('factCheckEditor.loading')}</span>
		</div>

	<!-- Error State -->
	{:else if loadError}
		<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
			<p class="text-red-700">{$t('factCheckEditor.loadError')}</p>
			<p class="text-red-600 text-sm mt-2">{loadError}</p>
		</div>

	<!-- Preview Mode -->
	{:else if showPreview}
		<div data-testid="preview-mode" class="space-y-6">
			<div class="flex justify-end">
				<button
					type="button"
					onclick={togglePreview}
					class="px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700"
				>
					{$t('factCheckEditor.actions.edit')}
				</button>
			</div>

			{#if claimText}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('factCheckEditor.claim.title')}</h3>
					<p class="text-gray-900 bg-gray-50 p-4 rounded">{claimText}</p>
				</div>
			{/if}

			<div>
				<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('factCheckEditor.analysis.title')}</h3>
				<div class="prose max-w-none bg-gray-50 p-4 rounded">
					{#if analysis}
						<p class="whitespace-pre-wrap">{analysis}</p>
					{:else}
						<p class="text-gray-500 italic">{$t('factCheckEditor.preview.noContent')}</p>
					{/if}
				</div>
			</div>

			{#if verdict}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('factCheckEditor.verdict.title')}</h3>
					<p class="text-gray-900">{$t(`ratings.${verdict}.name`)}</p>
				</div>
			{/if}
		</div>

	<!-- Editor Mode -->
	{:else}
		<form onsubmit={(e) => { e.preventDefault(); }} class="space-y-6">
			<!-- Success Message -->
			{#if successMessage}
				<div class="bg-green-50 border border-green-200 rounded-lg p-4">
					<p class="text-green-700">{successMessage}</p>
				</div>
			{/if}

			<!-- Claim Section (Read-only) -->
			{#if claimText}
				<div>
					<h3 class="text-sm font-medium text-gray-700 mb-2">{$t('factCheckEditor.claim.title')}</h3>
					<div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
						<p class="text-gray-900">{claimText}</p>
					</div>
				</div>
			{/if}

			<!-- Analysis Section -->
			<div>
				<label for="analysis" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('factCheckEditor.analysis.title')}
				</label>
				<textarea
					id="analysis"
					bind:value={analysis}
					oninput={handleInputChange}
					onblur={handleBlur}
					rows="8"
					placeholder={$t('factCheckEditor.analysis.placeholder')}
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
					class:border-red-500={validationErrors['analysis']}
				></textarea>
				<div class="flex justify-between mt-1">
					<div>
						{#if validationErrors['analysis']}
							<p class="text-red-600 text-sm">{validationErrors['analysis']}</p>
						{/if}
					</div>
					<div class="text-sm text-gray-500 flex gap-4">
						<span>{$t('factCheckEditor.analysis.charCount', { values: { count: charCount } })}</span>
						<span>{$t('factCheckEditor.analysis.wordCount', { values: { count: wordCount } })}</span>
					</div>
				</div>
			</div>

			<!-- Verdict Section -->
			<div>
				<label for="verdict" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('factCheckEditor.verdict.title')}
				</label>
				<select
					id="verdict"
					bind:value={verdict}
					onchange={handleInputChange}
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
					class:border-red-500={validationErrors['verdict']}
				>
					<option value="">{$t('factCheckEditor.verdict.select')}</option>
					{#each verdictOptions as option}
						<option value={option}>{$t(`ratings.${option}.name`)}</option>
					{/each}
				</select>
				{#if validationErrors['verdict']}
					<p class="text-red-600 text-sm mt-1">{validationErrors['verdict']}</p>
				{/if}
			</div>

			<!-- Justification Section -->
			<div>
				<label for="justification" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('factCheckEditor.justification.title')}
				</label>
				<textarea
					id="justification"
					bind:value={justification}
					oninput={handleInputChange}
					onblur={handleBlur}
					rows="4"
					placeholder={$t('factCheckEditor.justification.placeholder')}
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				></textarea>
			</div>

			<!-- Sources Section -->
			<div>
				<div class="flex items-center justify-between mb-2">
					<h3 class="text-sm font-medium text-gray-700">{$t('factCheckEditor.sources.title')}</h3>
					<button
						type="button"
						onclick={addSource}
						class="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
						{$t('factCheckEditor.sources.add')}
					</button>
				</div>

				{#if sources.length === 0}
					<p class="text-gray-500 text-sm italic">{$t('factCheckEditor.sources.empty')}</p>
				{:else}
					<div class="space-y-2">
						{#each sources as source, index}
							<div class="flex gap-2">
								<input
									type="text"
									value={source}
									oninput={(e) => updateSource(index, (e.target as HTMLInputElement).value)}
									onblur={handleBlur}
									placeholder={$t('factCheckEditor.sources.placeholder')}
									class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
								/>
								<button
									type="button"
									onclick={() => removeSource(index)}
									class="px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition"
									aria-label={$t('factCheckEditor.sources.remove')}
								>
									<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Internal Notes Section -->
			<div>
				<label for="internal-notes" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('factCheckEditor.notes.title')}
				</label>
				<textarea
					id="internal-notes"
					bind:value={internalNotes}
					oninput={handleInputChange}
					onblur={handleBlur}
					rows="3"
					placeholder={$t('factCheckEditor.notes.placeholder')}
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				></textarea>
			</div>

			<!-- Action Buttons -->
			<div class="flex items-center justify-between pt-4 border-t border-gray-200">
				<button
					type="button"
					onclick={togglePreview}
					class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
				>
					{$t('factCheckEditor.actions.preview')}
				</button>

				<div class="flex gap-3">
					<button
						type="button"
						onclick={handleSaveDraft}
						disabled={isSaving}
						class="px-4 py-2 text-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 disabled:opacity-50 transition"
					>
						{isSaving ? $t('factCheckEditor.actions.saving') : $t('factCheckEditor.actions.save')}
					</button>

					<button
						type="button"
						onclick={handleSubmitForReview}
						disabled={isSubmitting}
						class="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 transition"
					>
						{isSubmitting ? $t('factCheckEditor.actions.submitting') : $t('factCheckEditor.actions.submit')}
					</button>
				</div>
			</div>
		</form>
	{/if}
</div>
