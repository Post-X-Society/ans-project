<script lang="ts">
	import { t } from '$lib/i18n';
	import { getDraft, saveDraft } from '$lib/api/drafts';
	import { getSources } from '$lib/api/sources';
	import type { DraftResponse, DraftUpdate, FactCheckRatingValue, Source } from '$lib/api/types';

	interface Props {
		factCheckId: string;
		claimText?: string;
		onSubmitForReview?: () => void;
	}

	let { factCheckId, claimText = '', onSubmitForReview }: Props = $props();

	// Load sources for citation references
	let availableSources = $state<Source[]>([]);
	let loadingSources = $state(false);

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

	// Load draft and sources on mount
	$effect(() => {
		loadDraft();
		loadSources();
		return () => {
			if (autoSaveTimer) {
				clearTimeout(autoSaveTimer);
			}
		};
	});

	async function loadSources() {
		loadingSources = true;
		try {
			const response = await getSources(factCheckId);
			availableSources = response.sources || [];
		} catch (error) {
			console.error('Failed to load sources:', error);
		} finally {
			loadingSources = false;
		}
	}

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
				claim_summary: claimSummary.trim() || null,
				analysis: analysis.trim() || null,
				verdict: verdict || null,
				justification: justification.trim() || null,
				internal_notes: internalNotes.trim() || null
			};

			const response = await saveDraft(factCheckId, draftData);
			lastSavedAt = response.draft_updated_at;
			hasUnsavedChanges = false;
			successMessage = $t('factCheckEditor.success.saved');

			// Clear success message after 3 seconds
			setTimeout(() => {
				successMessage = null;
			}, 3000);
		} catch (error: any) {
			console.error('Failed to save draft:', error);
			// Log validation errors for debugging
			if (error.response?.data?.detail) {
				console.error('Validation errors:', error.response.data.detail);
				// Display validation errors to user
				if (Array.isArray(error.response.data.detail)) {
					const errorMessages = error.response.data.detail.map((e: any) =>
						`${e.loc?.join('.') || 'unknown'}: ${e.msg}`
					).join(', ');
					loadError = `Validation error: ${errorMessages}`;
				}
			}
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

	function insertCitation(citationNumber: number) {
		// Insert [citationNumber] at cursor position in the analysis textarea
		const textarea = document.getElementById('analysis') as HTMLTextAreaElement;
		if (!textarea) return;

		const start = textarea.selectionStart;
		const end = textarea.selectionEnd;
		const citation = `[${citationNumber}]`;

		// Update the analysis value
		const newValue = analysis.substring(0, start) + citation + analysis.substring(end);
		analysis = newValue;

		// Mark as changed
		hasUnsavedChanges = true;
		successMessage = null;

		// Focus and set cursor position after the inserted citation
		// Use requestAnimationFrame to ensure DOM has updated
		requestAnimationFrame(() => {
			textarea.focus();
			const newPosition = start + citation.length;
			textarea.setSelectionRange(newPosition, newPosition);
		});
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

			<!-- Analysis Section with Citation Helper -->
			<div>
				<div class="flex items-center justify-between mb-1">
					<label for="analysis" class="block text-sm font-medium text-gray-700">
						{$t('factCheckEditor.analysis.title')}
					</label>
					{#if availableSources.length > 0}
						<span class="text-xs text-gray-500">
							{$t('factCheckEditor.citations.helper')}
						</span>
					{/if}
				</div>

				<!-- Citation Reference Buttons -->
				{#if availableSources.length > 0}
					<div class="mb-2 p-2 bg-gray-50 border border-gray-200 rounded-lg">
						<div class="flex items-center gap-2 flex-wrap">
							<span class="text-xs font-medium text-gray-600">{$t('factCheckEditor.citations.insert')}:</span>
							{#each availableSources as source, index}
								<button
									type="button"
									onclick={() => insertCitation(index + 1)}
									class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-primary-100 text-primary-700 hover:bg-primary-200 transition-colors"
									title={source.title}
								>
									[{index + 1}] {source.title.length > 30 ? source.title.substring(0, 30) + '...' : source.title}
								</button>
							{/each}
						</div>
						<p class="text-xs text-gray-500 mt-1">
							{$t('factCheckEditor.citations.note')}
						</p>
					</div>
				{/if}

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
