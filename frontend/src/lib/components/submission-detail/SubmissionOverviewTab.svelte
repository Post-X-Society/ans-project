<!--
  SubmissionOverviewTab Component

  Issue #154: Fix TanStack Query reactivity issue
  Extracted from submissions/[id]/+page.svelte for modularity

  Features:
  - Displays submission info card with content, type, status, submitter
  - Shows Spotlight metadata when available
  - Renders workflow timeline
  - Lists assigned reviewers
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import WorkflowTimeline from '$lib/components/WorkflowTimeline.svelte';
	import WorkflowTransitionPanel from '$lib/components/WorkflowTransitionPanel.svelte';
	import { assignReviewer, removeReviewer } from '$lib/api/submissions';
	import { apiClient } from '$lib/api/client';
	import type {
		Submission,
		WorkflowHistoryResponse,
		WorkflowCurrentStateResponse,
		WorkflowState,
		UserRole,
		User
	} from '$lib/api/types';

	interface Props {
		submission: Submission;
		workflowHistory: WorkflowHistoryResponse | null;
		workflowState: WorkflowCurrentStateResponse | null;
		isLoadingHistory: boolean;
		historyError: string | null;
		userRole?: UserRole;
		onReviewersUpdated?: () => void;
		onTransitionClick?: (state: WorkflowState) => void;
		isSubmittingTransition?: boolean;
		transitionError?: string | null;
	}

	let {
		submission,
		workflowHistory,
		workflowState,
		isLoadingHistory,
		historyError,
		userRole,
		onReviewersUpdated,
		onTransitionClick,
		isSubmittingTransition = false,
		transitionError = null
	}: Props = $props();

	// State for reviewer management
	let availableReviewers = $state<User[]>([]);
	let isLoadingReviewers = $state(false);
	let isAssigning = $state(false);
	let showAssignDropdown = $state(false);
	let assignError = $state<string | null>(null);

	// State for manual claim addition (Issue #176)
	let showAddClaimForm = $state(false);
	let newClaimContent = $state('');
	let newClaimSource = $state('manual');
	let isSubmittingClaim = $state(false);
	let claimError = $state<string | null>(null);
	let claimSuccess = $state<string | null>(null);

	// Check if user can manage reviewers (admin or super_admin)
	let canManageReviewers = $derived(
		userRole === 'admin' || userRole === 'super_admin'
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
	 * Load available reviewers
	 */
	async function loadAvailableReviewers() {
		if (!canManageReviewers) return;

		isLoadingReviewers = true;
		assignError = null;

		try {
			const response = await apiClient.get<User[]>('/api/v1/users');
			// Filter to only show users with reviewer role or higher
			availableReviewers = response.data.filter(
				(user) => user.role === 'reviewer' || user.role === 'admin' || user.role === 'super_admin'
			);
		} catch (error) {
			console.error('Failed to load reviewers:', error);
			assignError = 'Failed to load available reviewers';
		} finally {
			isLoadingReviewers = false;
		}
	}

	/**
	 * Assign a reviewer to the submission
	 */
	async function handleAssignReviewer(reviewerId: string) {
		isAssigning = true;
		assignError = null;

		try {
			await assignReviewer(submission.id, reviewerId);
			showAssignDropdown = false;
			if (onReviewersUpdated) {
				await onReviewersUpdated();
			}
		} catch (error: any) {
			console.error('Failed to assign reviewer:', error);
			assignError = error.response?.data?.detail || error.message || 'Failed to assign reviewer';
		} finally {
			isAssigning = false;
		}
	}

	/**
	 * Remove a reviewer from the submission
	 */
	async function handleRemoveReviewer(reviewerId: string) {
		if (!confirm($t('submissions.detail.confirmRemoveReviewer'))) {
			return;
		}

		isAssigning = true;
		assignError = null;

		try {
			await removeReviewer(submission.id, reviewerId);
			onReviewersUpdated?.();
		} catch (error: any) {
			console.error('Failed to remove reviewer:', error);
			assignError = error.response?.data?.detail || 'Failed to remove reviewer';
		} finally {
			isAssigning = false;
		}
	}

	/**
	 * Get reviewers not yet assigned
	 */
	let unassignedReviewers = $derived.by(() => {
		const assigned = submission.reviewers?.map(r => r.id) || [];
		return availableReviewers.filter((reviewer) => !assigned.includes(reviewer.id));
	});

	/**
	 * Handle manual claim addition (Issue #176)
	 */
	async function handleAddClaim() {
		isSubmittingClaim = true;
		claimError = null;
		claimSuccess = null;

		try {
			const response = await apiClient.post(
				`/api/v1/submissions/${submission.id}/claims`,
				{
					content: newClaimContent,
					source: newClaimSource,
				}
			);

			// Show success message
			claimSuccess = 'Claim added successfully!';

			// Reset form after a short delay
			setTimeout(() => {
				showAddClaimForm = false;
				newClaimContent = '';
				newClaimSource = 'manual';
				claimSuccess = null;
			}, 1500);

			// Refresh submission data to show new claim
			if (onReviewersUpdated) {
				await onReviewersUpdated();
			}
		} catch (error: any) {
			console.error('Failed to add claim:', error);
			claimError = error.response?.data?.detail || error.message || 'Failed to add claim';
		} finally {
			isSubmittingClaim = false;
		}
	}
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-8" data-testid="overview-tab-container">
	<!-- Left Column: Submission Details -->
	<div class:lg:col-span-2={userRole !== 'submitter'} class:lg:col-span-3={userRole === 'submitter'} class="space-y-6">
		<!-- Submission Info Card -->
		<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="submission-info-card">
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
			</dl>

			<!-- Content URL -->
			<div class="mt-4 pt-4 border-t border-gray-100">
				<dt class="text-sm font-medium text-gray-500 mb-1">Content</dt>
				<dd class="text-gray-900 break-all">{submission.content}</dd>
			</div>
		</div>

		<!-- Spotlight Info Card (if applicable) -->
		{#if submission.spotlight_content}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="spotlight-info-card">
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

				<!-- Transcription Section (Issue #176) -->
				{#if submission.spotlight_content.transcription}
					<div class="mt-6 pt-6 border-t border-gray-100">
						<div class="flex items-center justify-between mb-3">
							<h3 class="text-lg font-medium text-gray-900">Transcription</h3>
							{#if submission.spotlight_content.transcription_language}
								<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
									{submission.spotlight_content.transcription_language.toUpperCase()}
									{#if submission.spotlight_content.transcription_confidence}
										({Math.round(submission.spotlight_content.transcription_confidence * 100)}%)
									{/if}
								</span>
							{/if}
						</div>
						<div class="bg-gray-50 rounded-lg p-4">
							<p class="text-sm text-gray-700 whitespace-pre-wrap">{submission.spotlight_content.transcription}</p>
						</div>
					</div>
				{:else}
					<div class="mt-6 pt-6 border-t border-gray-100">
						<p class="text-sm text-gray-500 italic">Transcription in progress...</p>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Claims Card (Issue #176) -->
		{#if submission.spotlight_content?.transcription}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="claims-card">
				<div class="flex items-center justify-between mb-4">
					<h2 class="text-xl font-semibold text-gray-900">
						Extracted Claims
						{#if submission.claims && submission.claims.length > 0}
							({submission.claims.length})
						{/if}
					</h2>
					{#if userRole && ['reviewer', 'admin', 'super_admin'].includes(userRole)}
						<button
							onclick={() => (showAddClaimForm = !showAddClaimForm)}
							class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
						>
							<svg class="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
							Add Claim Manually
						</button>
					{/if}
				</div>

				<!-- Manual Claim Addition Form (Issue #176) -->
				{#if showAddClaimForm}
					<div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
						<form onsubmit={(e) => { e.preventDefault(); handleAddClaim(); }}>
							<div class="space-y-3">
								<div>
									<label for="claim-content" class="block text-sm font-medium text-gray-700">Claim Content</label>
									<textarea
										id="claim-content"
										bind:value={newClaimContent}
										rows="3"
										class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
										placeholder="Enter the factual claim to be verified..."
										required
									></textarea>
								</div>
								<div>
									<label for="claim-source" class="block text-sm font-medium text-gray-700">Source</label>
									<select
										id="claim-source"
										bind:value={newClaimSource}
										class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
									>
										<option value="manual">Manual Entry</option>
										<option value="transcription">Transcription</option>
										<option value="comment">User Comment</option>
									</select>
								</div>
								{#if claimError}
									<div class="rounded-md bg-red-50 p-3">
										<p class="text-sm text-red-800">{claimError}</p>
									</div>
								{/if}
								{#if claimSuccess}
									<div class="rounded-md bg-green-50 p-3">
										<p class="text-sm text-green-800">{claimSuccess}</p>
									</div>
								{/if}
								<div class="flex justify-end gap-2">
									<button
										type="button"
										onclick={() => {
											showAddClaimForm = false;
											newClaimContent = '';
											claimError = null;
											claimSuccess = null;
										}}
										class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
									>
										Cancel
									</button>
									<button
										type="submit"
										disabled={isSubmittingClaim || !newClaimContent.trim()}
										class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
									>
										{isSubmittingClaim ? 'Adding...' : 'Add Claim'}
									</button>
								</div>
							</div>
						</form>
					</div>
				{/if}

				{#if submission.claims && submission.claims.length > 0}
					<!-- Claims found -->
					<div class="space-y-3">
						{#each submission.claims as claim, index}
							<div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition">
								<div class="flex items-start gap-3">
									<span class="flex-shrink-0 inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-800 text-xs font-medium">
										{index + 1}
									</span>
									<div class="flex-1">
										<p class="text-sm text-gray-900">{claim.content}</p>
										<div class="mt-2 flex items-center gap-3 text-xs text-gray-500">
											<span>Source: {claim.source}</span>
											{#if claim.language}
												<span>• Language: {claim.language}</span>
											{/if}
										</div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else if submission.claims && submission.claims.length === 0}
					<!-- Claims extraction completed but none found -->
					<div class="bg-gray-50 rounded-lg p-6 text-center">
						<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						<h3 class="mt-2 text-sm font-medium text-gray-900">No factual claims detected</h3>
						<p class="mt-1 text-sm text-gray-500">This content does not contain verifiable factual claims that require fact-checking.</p>
					</div>
				{:else}
					<!-- Claim extraction still in progress -->
					<div class="bg-blue-50 rounded-lg p-6 text-center">
						<svg class="animate-spin mx-auto h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						<p class="mt-3 text-sm text-gray-700 font-medium">Extracting claims from transcription...</p>
						<p class="mt-1 text-xs text-gray-500">This may take 30-60 seconds</p>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Workflow Timeline (hidden for submitters) -->
		{#if userRole !== 'submitter'}
			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="workflow-timeline-card">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">
					{$t('workflow.timeline.title')}
				</h2>

				<WorkflowTimeline
					history={workflowHistory?.items ?? []}
					currentState={workflowState?.current_state ?? 'submitted'}
					isLoading={isLoadingHistory}
					error={historyError}
				/>
			</div>
		{/if}
	</div>

	<!-- Right Column: Workflow Controls & Assigned Reviewers (hidden for submitters) -->
	{#if userRole !== 'submitter'}
		<div class="space-y-6">
			<!-- Workflow Transition Panel -->
			{#if workflowState?.current_state && workflowState?.valid_transitions && workflowState.valid_transitions.length > 0}
				<WorkflowTransitionPanel
					currentState={workflowState.current_state}
					validTransitions={workflowState.valid_transitions}
					userRole={userRole ?? 'submitter'}
					onTransitionClick={onTransitionClick ?? (() => {})}
					isLoading={isSubmittingTransition}
					error={transitionError}
				/>
			{/if}

			<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="assigned-reviewers-card">
				<div class="flex justify-between items-center mb-4">
					<h2 class="text-xl font-semibold text-gray-900">
						{$t('submissions.detail.assignedReviewers')}
					</h2>
					{#if canManageReviewers}
						<button
							onclick={() => {
								showAssignDropdown = !showAssignDropdown;
								if (showAssignDropdown && availableReviewers.length === 0) {
									loadAvailableReviewers();
								}
							}}
							class="text-sm text-blue-600 hover:text-blue-800 font-medium"
							disabled={isAssigning}
						>
							+ {$t('submissions.detail.assignReviewer')}
						</button>
					{/if}
				</div>

				{#if assignError}
					<div class="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
						{assignError}
					</div>
				{/if}

				<!-- Assign reviewer dropdown -->
				{#if showAssignDropdown && canManageReviewers}
					<div class="mb-4 p-3 bg-gray-50 border border-gray-200 rounded">
						<p class="text-sm font-medium text-gray-700 mb-2">
							{$t('submissions.detail.selectReviewer')}
						</p>
						{#if isLoadingReviewers}
							<p class="text-sm text-gray-500">{$t('common.loading')}...</p>
						{:else if unassignedReviewers.length === 0}
							<p class="text-sm text-gray-500">{$t('submissions.detail.noAvailableReviewers')}</p>
						{:else}
							<div class="space-y-1">
								{#each unassignedReviewers as reviewer}
									<button
										onclick={() => handleAssignReviewer(reviewer.id)}
										class="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
										disabled={isAssigning}
									>
										{#if isAssigning}
											<span class="text-gray-500">Assigning...</span>
										{:else}
											{reviewer.email}
										{/if}
									</button>
								{/each}
							</div>
						{/if}
					</div>
				{/if}

				<!-- Assigned reviewers list -->
				{#if submission.reviewers && submission.reviewers.length > 0}
					<div class="flex flex-wrap gap-2">
						{#each submission.reviewers as reviewer}
							<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
								{reviewer.email}
								{#if canManageReviewers}
									<button
										onclick={() => handleRemoveReviewer(reviewer.id)}
										class="ml-2 text-gray-500 hover:text-red-600 transition"
										disabled={isAssigning}
										aria-label={$t('submissions.detail.removeReviewer')}
									>
										×
									</button>
								{/if}
							</span>
						{/each}
					</div>
				{:else}
					<p class="text-gray-500 text-sm">{$t('submissions.detail.noReviewers')}</p>
				{/if}
			</div>
		</div>
	{/if}
</div>
