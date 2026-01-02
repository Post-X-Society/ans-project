<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { WorkflowHistoryItem, WorkflowState, PeerReviewStatusResponse, ApprovalStatus } from '$lib/api/types';

	interface Props {
		history: WorkflowHistoryItem[];
		currentState: WorkflowState;
		isLoading?: boolean;
		error?: string | null;
		peerReviewStatus?: PeerReviewStatusResponse | null;
		peerReviewLoading?: boolean;
	}

	let { history, currentState, isLoading = false, error = null, peerReviewStatus = null, peerReviewLoading = false }: Props = $props();

	/**
	 * Approval status color configuration
	 */
	const approvalColors: Record<ApprovalStatus, { bg: string; text: string }> = {
		approved: { bg: 'bg-green-100', text: 'text-green-700' },
		rejected: { bg: 'bg-red-100', text: 'text-red-700' },
		pending: { bg: 'bg-yellow-100', text: 'text-yellow-700' }
	};

	/**
	 * Get translated approval status
	 */
	function getApprovalStatusText(status: ApprovalStatus): string {
		return $t(`workflow.peerReview.${status}`);
	}

	/**
	 * State color configuration for visual distinction
	 */
	const stateColors: Record<WorkflowState, { bg: string; border: string; text: string }> = {
		submitted: { bg: 'bg-blue-100', border: 'border-blue-500', text: 'text-blue-700' },
		queued: { bg: 'bg-gray-100', border: 'border-gray-500', text: 'text-gray-700' },
		duplicate_detected: { bg: 'bg-orange-100', border: 'border-orange-500', text: 'text-orange-700' },
		archived: { bg: 'bg-slate-100', border: 'border-slate-500', text: 'text-slate-700' },
		assigned: { bg: 'bg-indigo-100', border: 'border-indigo-500', text: 'text-indigo-700' },
		in_research: { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-700' },
		draft_ready: { bg: 'bg-cyan-100', border: 'border-cyan-500', text: 'text-cyan-700' },
		needs_more_research: { bg: 'bg-amber-100', border: 'border-amber-500', text: 'text-amber-700' },
		admin_review: { bg: 'bg-purple-100', border: 'border-purple-500', text: 'text-purple-700' },
		peer_review: { bg: 'bg-violet-100', border: 'border-violet-500', text: 'text-violet-700' },
		final_approval: { bg: 'bg-teal-100', border: 'border-teal-500', text: 'text-teal-700' },
		published: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-700' },
		under_correction: { bg: 'bg-rose-100', border: 'border-rose-500', text: 'text-rose-700' },
		corrected: { bg: 'bg-emerald-100', border: 'border-emerald-500', text: 'text-emerald-700' },
		rejected: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-700' }
	};

	/**
	 * Get color configuration for a state with fallback
	 */
	function getStateColor(state: WorkflowState) {
		return stateColors[state] || stateColors.queued;
	}

	/**
	 * Format timestamp for display
	 */
	function formatTimestamp(isoString: string): string {
		const date = new Date(isoString);
		return date.toLocaleString(undefined, {
			dateStyle: 'medium',
			timeStyle: 'short'
		});
	}

	/**
	 * Get translated state name
	 */
	function getStateName(state: WorkflowState): string {
		return $t(`workflow.states.${state}`);
	}

	/**
	 * Check if item represents the current active state
	 */
	function isCurrentState(item: WorkflowHistoryItem): boolean {
		return item.to_state === currentState;
	}

	/**
	 * Sort history chronologically (oldest first)
	 */
	const sortedHistory = $derived(
		[...history].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
	);
</script>

{#if isLoading}
	<div class="flex items-center justify-center py-8">
		<div class="animate-pulse text-gray-500">
			{$t('workflow.timeline.loading')}
		</div>
	</div>
{:else if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
		{error}
	</div>
{:else if sortedHistory.length === 0}
	<div class="rounded-lg border border-gray-200 bg-gray-50 p-4 text-center text-gray-500">
		{$t('workflow.timeline.empty')}
	</div>
{:else}
	<ul
		role="list"
		aria-label={$t('workflow.timeline.ariaLabel')}
		class="timeline relative space-y-4"
	>
		{#each sortedHistory as item, index (item.id)}
			{@const colors = getStateColor(item.to_state)}
			{@const isCurrent = isCurrentState(item)}
			{@const isLast = index === sortedHistory.length - 1}

			<li
				class="relative flex gap-4 {isCurrent ? 'current' : ''}"
				aria-current={isCurrent ? 'step' : undefined}
			>
				<!-- Timeline connector line -->
				{#if !isLast}
					<div
						class="absolute left-4 top-8 -ml-px h-full w-0.5 bg-gray-200"
						aria-hidden="true"
					></div>
				{/if}

				<!-- State indicator dot -->
				<div class="relative flex h-8 w-8 flex-shrink-0 items-center justify-center">
					<div
						data-testid="timeline-indicator"
						class="h-4 w-4 rounded-full border-2 {colors.bg} {colors.border} {isCurrent
							? 'ring-2 ring-offset-2 ring-blue-500'
							: ''}"
						aria-hidden="true"
					></div>
				</div>

				<!-- Content -->
				<div class="flex-1 pb-4">
					<div class="flex flex-wrap items-center gap-2">
						<!-- State name badge -->
						<span
							class="inline-flex items-center rounded-full px-2.5 py-0.5 text-sm font-medium {colors.bg} {colors.text}"
						>
							{getStateName(item.to_state)}
						</span>

						{#if isCurrent}
							<span class="text-xs font-medium text-blue-600">
								({$t('workflow.timeline.currentState')})
							</span>
						{/if}
					</div>

					<!-- Actor and timestamp -->
					<div class="mt-1 flex flex-wrap items-center gap-x-3 text-sm text-gray-500">
						{#if item.transitioned_by}
							<span>
								{$t('workflow.timeline.transitionBy', {
									values: { actor: item.transitioned_by.email }
								})}
							</span>
						{/if}

						<time datetime={item.created_at} class="text-gray-400">
							{formatTimestamp(item.created_at)}
						</time>
					</div>

					<!-- Reason if provided -->
					{#if item.reason}
						<p class="mt-1 text-sm text-gray-600">
							{item.reason}
						</p>
					{/if}
				</div>
			</li>
		{/each}
	</ul>

	<!-- Peer Review Section -->
	{#if peerReviewLoading}
		<div class="mt-6 animate-pulse text-gray-500">
			{$t('workflow.peerReview.loading')}
		</div>
	{:else if peerReviewStatus}
		<div
			data-testid="peer-review-section"
			role="region"
			aria-label={$t('workflow.peerReview.ariaLabel')}
			class="mt-6 rounded-lg border border-violet-200 bg-violet-50 p-4"
		>
			<!-- Section Header -->
			<div class="mb-4 flex items-center justify-between">
				<h3 class="text-lg font-semibold text-violet-800">
					{$t('workflow.peerReview.title')}
				</h3>

				<!-- Consensus Badge -->
				{#if peerReviewStatus.consensus_reached}
					<span
						data-testid="consensus-badge"
						class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {peerReviewStatus.approved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}"
					>
						<svg class="mr-1.5 h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
							{#if peerReviewStatus.approved}
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
							{:else}
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
							{/if}
						</svg>
						{$t('workflow.peerReview.consensusReached')}
					</span>
				{:else if peerReviewStatus.pending_count > 0}
					<span
						data-testid="awaiting-reviews-indicator"
						class="inline-flex items-center rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800"
					>
						<svg class="mr-1.5 h-4 w-4 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
						</svg>
						{$t('workflow.peerReview.awaitingReviews')}
					</span>
				{/if}
			</div>

			<!-- Review Summary -->
			<div data-testid="peer-review-summary" class="mb-4 text-sm text-gray-600">
				{$t('workflow.peerReview.summary', {
					values: {
						approved: peerReviewStatus.approved_count,
						rejected: peerReviewStatus.rejected_count,
						pending: peerReviewStatus.pending_count
					}
				})}
			</div>

			<!-- Reviewers List -->
			<div
				data-testid="peer-reviewers-list"
				role="list"
				aria-label={$t('workflow.peerReview.reviewerDecisions')}
				class="space-y-3"
			>
				{#each peerReviewStatus.reviews as review (review.id)}
					{@const colors = approvalColors[review.approval_status]}
					<div
						data-testid="peer-review-card"
						role="listitem"
						class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm"
					>
						<div class="flex items-center justify-between">
							<!-- Reviewer Email -->
							<span class="font-medium text-gray-800">
								{review.reviewer?.email || review.reviewer_id}
							</span>

							<!-- Approval Status Badge -->
							<span
								class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {colors.bg} {colors.text}"
							>
								{getApprovalStatusText(review.approval_status)}
							</span>
						</div>

						<!-- Comments (Deliberation) -->
						{#if review.comments}
							<p
								data-testid="review-comment"
								class="mt-2 text-sm text-gray-600 italic"
							>
								"{review.comments}"
							</p>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}
{/if}
