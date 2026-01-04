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
	import type {
		Submission,
		WorkflowHistoryResponse,
		WorkflowCurrentStateResponse,
		WorkflowState
	} from '$lib/api/types';

	interface Props {
		submission: Submission;
		workflowHistory: WorkflowHistoryResponse | null;
		workflowState: WorkflowCurrentStateResponse | null;
		isLoadingHistory: boolean;
		historyError: string | null;
	}

	let {
		submission,
		workflowHistory,
		workflowState,
		isLoadingHistory,
		historyError
	}: Props = $props();

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
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-8" data-testid="overview-tab-container">
	<!-- Left Column: Submission Details -->
	<div class="lg:col-span-2 space-y-6">
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

		<!-- Workflow Timeline -->
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
	</div>

	<!-- Right Column: Assigned Reviewers -->
	<div class="space-y-6">
		<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6" data-testid="assigned-reviewers-card">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">
				{$t('submissions.detail.assignedReviewers')}
			</h2>
			{#if submission.reviewers && submission.reviewers.length > 0}
				<div class="flex flex-wrap gap-2">
					{#each submission.reviewers as reviewer}
						<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
							{reviewer.email}
						</span>
					{/each}
				</div>
			{:else}
				<p class="text-gray-500 text-sm">{$t('submissions.detail.noReviewers')}</p>
			{/if}
		</div>
	</div>
</div>
