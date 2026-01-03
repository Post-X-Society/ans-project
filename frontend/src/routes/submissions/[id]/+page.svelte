<!--
  Submission Detail Page

  Issue #154: Fixed TanStack Query v6 reactivity issue with Svelte 5
  by migrating to manual $state + onMount pattern.

  This page has been modularized into smaller components:
  - SubmissionOverviewTab: Displays submission info, spotlight data, workflow timeline
  - SubmissionRatingTab: Rating form, current rating, workflow transitions, history
  - WorkflowTransitionModal: Modal for confirming workflow state changes

  The page now uses direct API calls with $state instead of TanStack Query,
  matching the working pattern used in /admin/peer-review/+page.svelte.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$lib/i18n';
	import { authStore } from '$lib/stores/auth';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import TabNavigation from '$lib/components/TabNavigation.svelte';
	import SourceManagementInterface from '$lib/components/sources/SourceManagementInterface.svelte';
	import {
		SubmissionOverviewTab,
		SubmissionRatingTab,
		WorkflowTransitionModal
	} from '$lib/components/submission-detail';
	import { getSubmission } from '$lib/api/submissions';
	import { getWorkflowHistory, getWorkflowCurrentState, transitionWorkflowState } from '$lib/api/workflow';
	import {
		getSubmissionRatings,
		getCurrentRating,
		assignRating,
		getRatingDefinitions
	} from '$lib/api/ratings';
	import type { PageData } from './$types';
	import type {
		Submission,
		WorkflowHistoryResponse,
		WorkflowCurrentStateResponse,
		FactCheckRating,
		CurrentRatingResponse,
		RatingDefinition,
		WorkflowState,
		FactCheckRatingValue
	} from '$lib/api/types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let auth = $derived($authStore);

	// Derive the submission ID for reactivity
	let submissionId = $derived(data.id);

	// Tab state management
	let currentTab = $derived($page.url.searchParams.get('tab') || 'overview');

	// Data state (using $state instead of TanStack Query)
	let submission = $state<Submission | null>(null);
	let workflowHistory = $state<WorkflowHistoryResponse | null>(null);
	let workflowState = $state<WorkflowCurrentStateResponse | null>(null);
	let ratings = $state<FactCheckRating[]>([]);
	let currentRating = $state<CurrentRatingResponse | null>(null);
	let ratingDefinitions = $state<RatingDefinition[]>([]);

	// Loading states
	let isLoading = $state(true);
	let isLoadingHistory = $state(false);
	let isLoadingRating = $state(false);

	// Error states
	let hasError = $state(false);
	let errorMessage = $state('');

	// Mutation states
	let isSubmittingRating = $state(false);
	let isSubmittingTransition = $state(false);

	// Modal state for workflow transition
	let showTransitionModal = $state(false);
	let selectedTransition = $state<WorkflowState | null>(null);

	// Check if fact-check editor should be shown (in_research or draft_ready state)
	let showFactCheckEditor = $derived(
		auth.user &&
			['reviewer', 'admin', 'super_admin'].includes(auth.user.role) &&
			workflowState?.current_state &&
			['in_research', 'draft_ready'].includes(workflowState.current_state)
	);

	// Define tabs
	let tabs = $derived([
		{ id: 'overview', label: $t('submissions.tabs.overview') },
		{ id: 'rating', label: $t('submissions.tabs.rating') },
		{ id: 'sources', label: $t('submissions.tabs.sources') },
		...(submission?.peer_review_triggered ? [{ id: 'peer-reviews', label: $t('submissions.tabs.peerReviews') }] : [])
	]);

	/**
	 * Load all submission data
	 */
	async function loadData() {
		if (!submissionId) return;

		isLoading = true;
		hasError = false;
		errorMessage = '';

		try {
			// Load submission and workflow state in parallel
			const [submissionData, workflowStateData] = await Promise.all([
				getSubmission(submissionId),
				getWorkflowCurrentState(submissionId)
			]);

			submission = submissionData;
			workflowState = workflowStateData;

			// Load additional data in parallel
			await Promise.all([
				loadWorkflowHistory(),
				loadRatings(),
				loadRatingDefinitions()
			]);
		} catch (err: unknown) {
			console.error('Error loading submission data:', err);
			hasError = true;
			errorMessage = err instanceof Error ? err.message : $t('submissions.detail.error');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Load workflow history
	 */
	async function loadWorkflowHistory() {
		if (!submissionId) return;

		isLoadingHistory = true;
		try {
			workflowHistory = await getWorkflowHistory(submissionId);
		} catch (err: unknown) {
			console.error('Error loading workflow history:', err);
		} finally {
			isLoadingHistory = false;
		}
	}

	/**
	 * Load ratings data
	 */
	async function loadRatings() {
		if (!submissionId) return;

		isLoadingRating = true;
		try {
			const [ratingsData, currentRatingData] = await Promise.all([
				getSubmissionRatings(submissionId),
				getCurrentRating(submissionId)
			]);
			ratings = ratingsData;
			currentRating = currentRatingData;
		} catch (err: unknown) {
			console.error('Error loading ratings:', err);
		} finally {
			isLoadingRating = false;
		}
	}

	/**
	 * Load rating definitions
	 */
	async function loadRatingDefinitions() {
		try {
			const response = await getRatingDefinitions();
			ratingDefinitions = response.items;
		} catch (err: unknown) {
			console.error('Error loading rating definitions:', err);
		}
	}

	/**
	 * Handle tab change with URL state management
	 */
	function handleTabChange(tabId: string) {
		const url = new URL($page.url);
		url.searchParams.set('tab', tabId);
		goto(url.toString(), { replaceState: false, noScroll: true });
	}

	/**
	 * Handle rating submission
	 */
	async function handleRatingSubmit(rating: FactCheckRatingValue, justification: string) {
		if (!submissionId) return;

		isSubmittingRating = true;
		try {
			await assignRating(submissionId, { rating, justification });
			// Refresh ratings data
			await loadRatings();
		} catch (err: unknown) {
			console.error('Error submitting rating:', err);
		} finally {
			isSubmittingRating = false;
		}
	}

	/**
	 * Open transition modal
	 */
	function openTransitionModal(state: WorkflowState) {
		selectedTransition = state;
		showTransitionModal = true;
	}

	/**
	 * Handle workflow transition
	 */
	async function handleTransition(reason: string) {
		if (!selectedTransition || !submissionId) return;

		isSubmittingTransition = true;
		try {
			await transitionWorkflowState(submissionId, {
				to_state: selectedTransition,
				reason: reason || undefined
			});
			showTransitionModal = false;
			selectedTransition = null;
			// Refresh workflow data
			const [newWorkflowState, newWorkflowHistory] = await Promise.all([
				getWorkflowCurrentState(submissionId),
				getWorkflowHistory(submissionId)
			]);
			workflowState = newWorkflowState;
			workflowHistory = newWorkflowHistory;
		} catch (err: unknown) {
			console.error('Error transitioning workflow:', err);
		} finally {
			isSubmittingTransition = false;
		}
	}

	/**
	 * Handle fact-check submission for review
	 */
	async function handleFactCheckSubmit() {
		// Refresh workflow data after fact-check submission
		if (!submissionId) return;
		try {
			const [newWorkflowState, newWorkflowHistory] = await Promise.all([
				getWorkflowCurrentState(submissionId),
				getWorkflowHistory(submissionId)
			]);
			workflowState = newWorkflowState;
			workflowHistory = newWorkflowHistory;
		} catch (err: unknown) {
			console.error('Error refreshing workflow data:', err);
		}
	}

	/**
	 * Retry loading data
	 */
	function handleRetry() {
		loadData();
	}

	// Load data on mount
	onMount(() => {
		loadData();
	});
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

			<!-- Tab Navigation -->
			<TabNavigation {tabs} activeTab={currentTab} onTabChange={handleTabChange} />

			<!-- Tab Content -->
			<div class="mt-6" data-testid="submission-detail-layout">
				<!-- Overview Tab -->
				{#if currentTab === 'overview'}
					<SubmissionOverviewTab
						{submission}
						{workflowHistory}
						{workflowState}
						{isLoadingHistory}
						historyError={null}
					/>

				<!-- Rating & Review Tab -->
				{:else if currentTab === 'rating'}
					<SubmissionRatingTab
						{submission}
						{submissionId}
						{workflowState}
						{currentRating}
						{ratings}
						{ratingDefinitions}
						user={auth.user}
						{isLoadingRating}
						showFactCheckEditor={showFactCheckEditor ?? false}
						onRatingSubmit={handleRatingSubmit}
						onTransitionClick={openTransitionModal}
						{isSubmittingRating}
						onFactCheckSubmit={handleFactCheckSubmit}
					/>

				<!-- Sources Tab -->
				{:else if currentTab === 'sources'}
					<SourceManagementInterface factCheckId={submission.fact_check_id ?? submissionId} />

				<!-- Peer Reviews Tab -->
				{:else if currentTab === 'peer-reviews'}
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
						<h2 class="text-xl font-semibold text-gray-900 mb-4">
							{$t('submissions.tabs.peerReviews')}
						</h2>
						<p class="text-gray-500">Peer review functionality coming soon...</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<!-- Workflow Transition Modal -->
<WorkflowTransitionModal
	show={showTransitionModal}
	targetState={selectedTransition}
	isSubmitting={isSubmittingTransition}
	onConfirm={handleTransition}
	onCancel={() => { showTransitionModal = false; selectedTransition = null; }}
/>
