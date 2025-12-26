<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { WorkflowHistoryItem, WorkflowState } from '$lib/api/types';

	interface Props {
		history: WorkflowHistoryItem[];
		currentState: WorkflowState;
		isLoading?: boolean;
		error?: string | null;
	}

	let { history, currentState, isLoading = false, error = null }: Props = $props();

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
{/if}
