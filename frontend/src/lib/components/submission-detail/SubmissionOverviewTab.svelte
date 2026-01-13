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
	}

	let {
		submission,
		workflowHistory,
		workflowState,
		isLoadingHistory,
		historyError,
		userRole,
		onReviewersUpdated
	}: Props = $props();

	// State for reviewer management
	let availableReviewers = $state<User[]>([]);
	let isLoadingReviewers = $state(false);
	let isAssigning = $state(false);
	let showAssignDropdown = $state(false);
	let assignError = $state<string | null>(null);

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
		console.log('Assigning reviewer:', reviewerId, 'to submission:', submission.id);
		isAssigning = true;
		assignError = null;

		try {
			const result = await assignReviewer(submission.id, reviewerId);
			console.log('Assignment result:', result);
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
		console.log('Assigned reviewer IDs:', assigned);
		console.log('Available reviewers:', availableReviewers.map(r => ({ id: r.id, email: r.email })));
		const unassigned = availableReviewers.filter(
			(reviewer) => !assigned.includes(reviewer.id)
		);
		console.log('Unassigned reviewers:', unassigned.map(r => ({ id: r.id, email: r.email })));
		return unassigned;
	});
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

	<!-- Right Column: Assigned Reviewers (hidden for submitters) -->
	{#if userRole !== 'submitter'}
		<div class="space-y-6">
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
