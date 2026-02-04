<!--
  SubmissionRatingTab Component

  Issue #154: Fix TanStack Query reactivity issue
  Extracted from submissions/[id]/+page.svelte for modularity

  Features:
  - Rating assignment form for reviewers/admins
  - Current rating display with justification
  - Workflow transition controls for admins
  - Rating history display
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import RatingBadge from '$lib/components/RatingBadge.svelte';
	import RatingDefinition from '$lib/components/RatingDefinition.svelte';
	import FactCheckEditor from '$lib/components/FactCheckEditor.svelte';
	import type {
		Submission,
		WorkflowCurrentStateResponse,
		WorkflowState,
		FactCheckRating,
		CurrentRatingResponse,
		RatingDefinition as RatingDefinitionType,
		User,
		FactCheckRatingValue
	} from '$lib/api/types';

	interface Props {
		submission: Submission;
		submissionId: string;
		workflowState: WorkflowCurrentStateResponse | null;
		currentRating: CurrentRatingResponse | null;
		ratings: FactCheckRating[];
		ratingDefinitions?: RatingDefinitionType[];
		user: User | null;
		isLoadingRating: boolean;
		showFactCheckEditor: boolean;
		onRatingSubmit: (rating: FactCheckRatingValue, justification: string) => void;
		isSubmittingRating: boolean;
		onFactCheckSubmit?: () => void;
	}

	let {
		submission,
		submissionId,
		workflowState,
		currentRating,
		ratings,
		ratingDefinitions = [],
		user,
		isLoadingRating,
		showFactCheckEditor,
		onRatingSubmit,
		isSubmittingRating,
		onFactCheckSubmit
	}: Props = $props();

	// Form state for rating assignment
	let selectedRating = $state<FactCheckRatingValue | ''>('');
	let justification = $state('');
	let ratingFormError = $state('');

	// Check if user can assign official EFCSN rating
	// Rating assignment is ONLY allowed in FINAL_APPROVAL stage (Super Admin)
	// This is when the official rating is assigned before publication
	let canAssignRating = $derived(
		user &&
			user.role === 'super_admin' &&
			workflowState?.current_state === 'final_approval'
	);

	/**
	 * Format date for display
	 */
	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleString();
	}

	/**
	 * Validate rating form
	 */
	function validateRatingForm(): boolean {
		if (!selectedRating) {
			ratingFormError = $t('submissions.rating.selectRatingError');
			return false;
		}
		if (justification.length < 50) {
			ratingFormError = $t('submissions.rating.justificationMinLength');
			return false;
		}
		ratingFormError = '';
		return true;
	}

	/**
	 * Handle rating submission
	 */
	function handleRatingSubmit() {
		if (!validateRatingForm() || !selectedRating) return;
		onRatingSubmit(selectedRating, justification);
		// Reset form on success (parent will handle the actual API call)
		selectedRating = '';
		justification = '';
		ratingFormError = '';
	}
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-8" data-testid="rating-tab-container">
	<!-- Left Column: Rating Assignment & Fact-Check Editor -->
	<div class="lg:col-span-2 space-y-6">
		<!-- Fact-Check Editor (shown in in_research or draft_ready states) - Issue #180 -->
		{#if showFactCheckEditor}
			{#if submission.fact_check_id}
				<!-- FactCheckEditor component has its own data-testid="fact-check-editor" -->
				<FactCheckEditor
					factCheckId={submission.fact_check_id}
					claimText={submission.content}
					onSubmitForReview={onFactCheckSubmit}
				/>
			{:else}
				<!-- No fact-check available yet -->
				<div class="bg-amber-50 rounded-lg shadow-sm border border-amber-200 p-6" data-testid="no-fact-check-message">
					<div class="flex items-start">
						<svg class="h-6 w-6 text-amber-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
						</svg>
						<div>
							<h3 class="text-lg font-semibold text-amber-800">
								{$t('factCheckEditor.noFactCheck.title')}
							</h3>
							<p class="mt-1 text-sm text-amber-700">
								{$t('factCheckEditor.noFactCheck.message')}
							</p>
						</div>
					</div>
				</div>
			{/if}
		{/if}

		<!-- Rating Assignment Form -->
		{#if canAssignRating}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="rating-form">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">
					{$t('submissions.rating.assignRating')}
				</h2>

				<form onsubmit={(e) => { e.preventDefault(); handleRatingSubmit(); }}>
					<!-- Rating Select -->
					<div class="mb-4">
						<label for="rating-select" class="block text-sm font-medium text-gray-700 mb-1">
							{$t('submissions.rating.title')}
						</label>
						<select
							id="rating-select"
							bind:value={selectedRating}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
						>
							<option value="">{$t('submissions.rating.selectRating')}</option>
							{#each ratingDefinitions as def}
								<option value={def.rating}>
									{$t(`ratings.${def.rating}.name`)}
								</option>
							{/each}
							{#if ratingDefinitions.length === 0}
								<option value="true">{$t('ratings.true.name')}</option>
								<option value="partly_false">{$t('ratings.partly_false.name')}</option>
								<option value="false">{$t('ratings.false.name')}</option>
								<option value="missing_context">{$t('ratings.missing_context.name')}</option>
								<option value="altered">{$t('ratings.altered.name')}</option>
								<option value="satire">{$t('ratings.satire.name')}</option>
								<option value="unverifiable">{$t('ratings.unverifiable.name')}</option>
							{/if}
						</select>
					</div>

					<!-- Justification Textarea -->
					<div class="mb-4">
						<label for="justification" class="block text-sm font-medium text-gray-700 mb-1">
							{$t('submissions.rating.justification')}
						</label>
						<textarea
							id="justification"
							bind:value={justification}
							rows="4"
							placeholder={$t('submissions.rating.justificationPlaceholder')}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
						></textarea>
						<p class="mt-1 text-xs text-gray-500">
							{justification.length}/50 {$t('submissions.rating.justificationMinLength').replace('Justification must be at least 50 characters', 'characters minimum')}
						</p>
					</div>

					<!-- Error Message -->
					{#if ratingFormError}
						<p class="text-red-600 text-sm mb-4">{ratingFormError}</p>
					{/if}

					<!-- Submit Button -->
					<button
						type="submit"
						disabled={isSubmittingRating}
						class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
					>
						{isSubmittingRating ? $t('submissions.rating.submitting') : $t('submissions.rating.submitRating')}
					</button>
				</form>
			</div>
		{/if}
	</div>

	<!-- Right Column: Current Rating, History, & Transitions -->
	<div class="space-y-6">
		<!-- Current Rating Card -->
		<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="current-rating-card">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">
				{$t('submissions.rating.current')}
			</h2>

			{#if isLoadingRating}
				<div class="flex items-center text-gray-500">
					<svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
					</svg>
					{$t('submissions.detail.loadingRatings')}
				</div>
			{:else if currentRating?.rating}
				<div class="space-y-4">
					<RatingDefinition
						rating={currentRating.rating.rating}
						size="lg"
					/>
					<div class="text-sm text-gray-600">
						<p class="font-medium mb-1">{$t('submissions.rating.justification')}:</p>
						<p class="text-gray-700">{currentRating.rating.justification}</p>
					</div>
					<p class="text-xs text-gray-500" data-testid="rating-timestamp">
						<time datetime={currentRating.rating.created_at}>
							{formatDate(currentRating.rating.created_at)}
						</time>
					</p>
				</div>
			{:else}
				<p class="text-gray-500" role="status" aria-live="polite">
					{$t('submissions.rating.noRating')}
				</p>
			{/if}
		</div>

		<!-- Rating History -->
		{#if ratings.length > 0}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="rating-history-card">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">
					{$t('submissions.rating.history')}
				</h2>

				<div class="space-y-4">
					{#each ratings as rating}
						<div class="border-l-4 border-gray-200 pl-4 py-2" class:border-primary-500={rating.is_current}>
							<div class="flex items-center justify-between mb-2">
								<RatingBadge rating={rating.rating} size="sm" />
								<span class="text-xs text-gray-500">
									{$t('submissions.rating.version', { values: { version: rating.version } })}
								</span>
							</div>
							<p class="text-sm text-gray-700 mb-1">{rating.justification}</p>
							<p class="text-xs text-gray-500" data-testid="rating-timestamp">
								<time datetime={rating.created_at}>
									{formatDate(rating.created_at)}
								</time>
							</p>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
