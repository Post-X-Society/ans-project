<script lang="ts">
	import { t } from '$lib/i18n';
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { authStore } from '$lib/stores/auth';
	import WorkflowTimeline from '$lib/components/WorkflowTimeline.svelte';
	import RatingBadge from '$lib/components/RatingBadge.svelte';
	import RatingDefinition from '$lib/components/RatingDefinition.svelte';
	import {
		submissionQueryOptions,
		workflowHistoryQueryOptions,
		workflowCurrentStateQueryOptions,
		workflowTransitionMutationOptions,
		submissionRatingsQueryOptions,
		currentRatingQueryOptions,
		ratingDefinitionsQueryOptions,
		assignRatingMutationOptions
	} from '$lib/api/queries';
	import type { PageData } from './$types';
	import type { FactCheckRatingValue, WorkflowState } from '$lib/api/types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let auth = $derived($authStore);
	const queryClient = useQueryClient();

	// Derive the submission ID for reactivity
	let submissionId = $derived(data.id);

	// Query for submission details
	const submissionQuery = createQuery(() => submissionQueryOptions(submissionId));

	// Query for workflow history
	const workflowHistoryQuery = createQuery(() => workflowHistoryQueryOptions(submissionId));

	// Query for current workflow state and valid transitions
	const workflowStateQuery = createQuery(() => workflowCurrentStateQueryOptions(submissionId));

	// Query for rating history
	const ratingsQuery = createQuery(() => submissionRatingsQueryOptions(submissionId));

	// Query for current rating
	const currentRatingQuery = createQuery(() => currentRatingQueryOptions(submissionId));

	// Query for rating definitions
	const ratingDefinitionsQuery = createQuery(() => ratingDefinitionsQueryOptions());

	// Mutation for workflow transition
	const workflowTransitionMutation = createMutation(() => workflowTransitionMutationOptions(submissionId));

	// Mutation for assigning rating
	const assignRatingMutation = createMutation(() => assignRatingMutationOptions(submissionId));

	// Form state for rating assignment
	let selectedRating = $state<FactCheckRatingValue | ''>('');
	let justification = $state('');
	let ratingFormError = $state('');

	// Form state for workflow transition
	let selectedTransition = $state<WorkflowState | null>(null);
	let transitionReason = $state('');
	let showTransitionModal = $state(false);

	// Derived values
	let submission = $derived($submissionQuery.data);
	let workflowHistory = $derived($workflowHistoryQuery.data);
	let workflowState = $derived($workflowStateQuery.data);
	let ratings = $derived($ratingsQuery.data ?? []);
	let currentRating = $derived($currentRatingQuery.data);
	let ratingDefinitions = $derived($ratingDefinitionsQuery.data?.items ?? []);

	let isLoading = $derived(
		$submissionQuery.isPending ||
			$workflowHistoryQuery.isPending ||
			$workflowStateQuery.isPending
	);

	let hasError = $derived($submissionQuery.isError);
	let errorMessage = $derived(
		$submissionQuery.error?.message ?? $t('submissions.detail.error')
	);

	// Check if user can assign ratings (reviewer, admin, super_admin)
	let canAssignRating = $derived(
		auth.user &&
			['reviewer', 'admin', 'super_admin'].includes(auth.user.role) &&
			workflowState?.current_state &&
			!['published', 'rejected', 'archived'].includes(workflowState.current_state)
	);

	// Check if user can transition workflow (admin, super_admin)
	let canTransition = $derived(
		auth.user &&
			['admin', 'super_admin'].includes(auth.user.role) &&
			workflowState?.valid_transitions &&
			workflowState.valid_transitions.length > 0
	);

	/**
	 * Format date for display
	 */
	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleString();
	}

	/**
	 * Format duration from milliseconds
	 */
	function formatDuration(ms: number | undefined | null): string {
		if (!ms) return '-';
		const seconds = Math.floor(ms / 1000);
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
	}

	/**
	 * Format view count
	 */
	function formatViewCount(count: number | undefined | null): string {
		if (!count) return '0';
		return count.toLocaleString();
	}

	/**
	 * Get content type label
	 */
	function getContentTypeLabel(type: string): string {
		return $t(`submissions.snapchatSpotlight`) || type;
	}

	/**
	 * Get translated workflow state label
	 */
	function getStateLabel(state: WorkflowState): string {
		return $t(`workflow.states.${state}`) || state;
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
	async function handleRatingSubmit() {
		if (!validateRatingForm() || !selectedRating) return;

		$assignRatingMutation.mutate(
			{
				rating: selectedRating,
				justification
			},
			{
				onSuccess: () => {
					// Reset form
					selectedRating = '';
					justification = '';
					ratingFormError = '';
					// Invalidate queries to refresh data
					queryClient.invalidateQueries({ queryKey: ['submissions', data.id, 'ratings'] });
				},
				onError: (error) => {
					ratingFormError = error.message || $t('submissions.rating.ratingError');
				}
			}
		);
	}

	/**
	 * Open transition modal
	 */
	function openTransitionModal(state: WorkflowState) {
		selectedTransition = state;
		transitionReason = '';
		showTransitionModal = true;
	}

	/**
	 * Handle workflow transition
	 */
	async function handleTransition() {
		if (!selectedTransition) return;

		$workflowTransitionMutation.mutate(
			{
				to_state: selectedTransition,
				reason: transitionReason || undefined
			},
			{
				onSuccess: () => {
					showTransitionModal = false;
					selectedTransition = null;
					transitionReason = '';
					// Invalidate queries to refresh data
					queryClient.invalidateQueries({ queryKey: ['workflow', data.id] });
				}
			}
		);
	}

	/**
	 * Retry loading data
	 */
	function handleRetry() {
		$submissionQuery.refetch();
		$workflowHistoryQuery.refetch();
		$workflowStateQuery.refetch();
		$ratingsQuery.refetch();
		$currentRatingQuery.refetch();
	}
</script>

<div class="container mx-auto px-4 py-8" data-testid="submission-detail-container">
	<!-- Back link -->
	<a
		href="/submissions"
		class="inline-flex items-center text-primary-600 hover:text-primary-700 mb-6"
	>
		<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
		</svg>
		{$t('submissions.detail.backToList')}
	</a>

	<!-- Loading State -->
	{#if isLoading}
		<div class="flex items-center justify-center py-12" role="status" aria-live="polite">
			<svg
				class="animate-spin h-8 w-8 text-primary-600 mr-3"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
			>
				<circle
					class="opacity-25"
					cx="12"
					cy="12"
					r="10"
					stroke="currentColor"
					stroke-width="4"
				></circle>
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				></path>
			</svg>
			<span class="text-lg text-gray-600">{$t('submissions.detail.loading')}</span>
		</div>

	<!-- Error State -->
	{:else if hasError}
		<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
			<svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<p class="text-red-700 mb-4">{errorMessage}</p>
			<button
				onclick={handleRetry}
				class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
			>
				{$t('common.tryAgain')}
			</button>
		</div>

	<!-- Content -->
	{:else if submission}
		<div class="max-w-7xl mx-auto">
			<!-- Page Header -->
			<div class="mb-8">
				<h1 class="text-3xl font-bold text-gray-900 mb-2">
					{$t('submissions.detail.title')}
				</h1>
				<p class="text-gray-500">
					{$t('submissions.detail.pageTitle', { values: { id: submission.id.slice(0, 8) } })}
				</p>
			</div>

			<!-- Main Layout -->
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-8" data-testid="submission-detail-layout">
				<!-- Left Column: Submission Details -->
				<div class="lg:col-span-2 space-y-6">
					<!-- Submission Info Card -->
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">
							{$t('submissions.detail.title')}
						</h2>

						<dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
							<!-- Content Type -->
							<div>
								<dt class="text-sm font-medium text-gray-500">
									{$t('submissions.detail.contentType')}
								</dt>
								<dd class="mt-1">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
										{getContentTypeLabel(submission.submission_type)}
									</span>
								</dd>
							</div>

							<!-- Current Status -->
							<div>
								<dt class="text-sm font-medium text-gray-500">
									{$t('submissions.detail.currentStatus')}
								</dt>
								<dd class="mt-1">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
										{workflowState ? getStateLabel(workflowState.current_state) : submission.status}
									</span>
								</dd>
							</div>

							<!-- Submitted By -->
							<div>
								<dt class="text-sm font-medium text-gray-500">
									{$t('submissions.detail.submittedBy')}
								</dt>
								<dd class="mt-1 text-gray-900">
									{submission.user?.email ?? '-'}
								</dd>
							</div>

							<!-- Submitted At -->
							<div>
								<dt class="text-sm font-medium text-gray-500">
									{$t('submissions.detail.submittedAt')}
								</dt>
								<dd class="mt-1 text-gray-900">
									<time datetime={submission.created_at}>
										{formatDate(submission.created_at)}
									</time>
								</dd>
							</div>

							<!-- Last Updated -->
							<div>
								<dt class="text-sm font-medium text-gray-500">
									{$t('submissions.detail.lastUpdated')}
								</dt>
								<dd class="mt-1 text-gray-900">
									<time datetime={submission.updated_at}>
										{formatDate(submission.updated_at)}
									</time>
								</dd>
							</div>

							<!-- Assigned Reviewers -->
							<div>
								<dt class="text-sm font-medium text-gray-500">
									{$t('submissions.detail.assignedReviewers')}
								</dt>
								<dd class="mt-1">
									{#if submission.reviewers && submission.reviewers.length > 0}
										<div class="flex flex-wrap gap-1">
											{#each submission.reviewers as reviewer}
												<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
													{reviewer.email}
												</span>
											{/each}
										</div>
									{:else}
										<span class="text-gray-500 text-sm">{$t('submissions.detail.noReviewers')}</span>
									{/if}
								</dd>
							</div>
						</dl>

						<!-- Content URL -->
						<div class="mt-4 pt-4 border-t border-gray-100">
							<dt class="text-sm font-medium text-gray-500 mb-1">Content</dt>
							<dd class="text-gray-900 break-all">{submission.content}</dd>
						</div>
					</div>

					<!-- Spotlight Info Card (if applicable) -->
					{#if submission.spotlight_content}
						<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
							<h2 class="text-xl font-semibold text-gray-900 mb-4">
								{$t('submissions.detail.spotlightInfo')}
							</h2>

							<div class="flex flex-col sm:flex-row gap-6">
								<!-- Thumbnail -->
								{#if submission.spotlight_content.thumbnail_url}
									<div class="flex-shrink-0">
										<img
											src={submission.spotlight_content.thumbnail_url}
											alt={$t('submissions.detail.thumbnail')}
											class="w-32 h-56 object-cover rounded-lg"
										/>
									</div>
								{/if}

								<!-- Metadata -->
								<dl class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
									<div>
										<dt class="text-sm font-medium text-gray-500">
											{$t('submissions.detail.creator')}
										</dt>
										<dd class="mt-1 text-gray-900">
											{submission.spotlight_content.creator_name || submission.spotlight_content.creator_username || $t('submissions.unknownCreator')}
										</dd>
									</div>

									<div>
										<dt class="text-sm font-medium text-gray-500">
											{$t('submissions.detail.viewCount')}
										</dt>
										<dd class="mt-1 text-gray-900">
											{formatViewCount(submission.spotlight_content.view_count)}
										</dd>
									</div>

									<div>
										<dt class="text-sm font-medium text-gray-500">
											{$t('submissions.detail.duration')}
										</dt>
										<dd class="mt-1 text-gray-900">
											{formatDuration(submission.spotlight_content.duration_ms)}
										</dd>
									</div>
								</dl>
							</div>
						</div>
					{/if}

					<!-- Workflow Timeline -->
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">
							{$t('workflow.timeline.title')}
						</h2>

						<WorkflowTimeline
							history={workflowHistory?.items ?? []}
							currentState={workflowState?.current_state ?? 'submitted'}
							isLoading={$workflowHistoryQuery.isPending}
							error={$workflowHistoryQuery.error?.message}
						/>
					</div>
				</div>

				<!-- Right Column: Actions & Rating -->
				<div class="space-y-6">
					<!-- Current Rating Card -->
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">
							{$t('submissions.rating.current')}
						</h2>

						{#if $currentRatingQuery.isPending}
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

					<!-- Rating Assignment Form -->
					{#if canAssignRating}
						<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
									disabled={$assignRatingMutation.isPending}
									class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
								>
									{$assignRatingMutation.isPending ? $t('submissions.rating.submitting') : $t('submissions.rating.submitRating')}
								</button>
							</form>
						</div>
					{/if}

					<!-- Workflow Transitions -->
					{#if canTransition && workflowState}
						<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
							<h2 class="text-xl font-semibold text-gray-900 mb-4">
								{$t('submissions.transition.title')}
							</h2>

							<p class="text-sm text-gray-600 mb-4">
								{$t('submissions.transition.validTransitions')}
							</p>

							<div class="space-y-2">
								{#each workflowState.valid_transitions as transition}
									<button
										onclick={() => openTransitionModal(transition)}
										class="w-full px-4 py-2 text-left border border-gray-300 rounded-lg hover:bg-gray-50 transition flex items-center justify-between"
									>
										<span>{getStateLabel(transition)}</span>
										<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
										</svg>
									</button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Rating History -->
					{#if ratings.length > 0}
						<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
		</div>
	{/if}
</div>

<!-- Transition Modal -->
{#if showTransitionModal && selectedTransition}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
			<h3 class="text-lg font-semibold text-gray-900 mb-4">
				{$t('submissions.transition.title')}
			</h3>

			<p class="text-gray-600 mb-4">
				Transition to: <strong>{getStateLabel(selectedTransition)}</strong>
			</p>

			<div class="mb-4">
				<label for="transition-reason" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('submissions.transition.reason')}
				</label>
				<textarea
					id="transition-reason"
					bind:value={transitionReason}
					rows="3"
					placeholder={$t('submissions.transition.reasonPlaceholder')}
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				></textarea>
			</div>

			<div class="flex gap-3">
				<button
					onclick={() => { showTransitionModal = false; selectedTransition = null; }}
					class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
				>
					{$t('common.cancel')}
				</button>
				<button
					onclick={handleTransition}
					disabled={$workflowTransitionMutation.isPending}
					class="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition"
				>
					{$workflowTransitionMutation.isPending ? $t('submissions.transition.confirming') : $t('submissions.transition.confirm')}
				</button>
			</div>
		</div>
	</div>
{/if}
