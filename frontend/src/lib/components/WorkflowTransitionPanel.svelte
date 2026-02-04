<!--
  WorkflowTransitionPanel Component

  Issue #179: Workflow Transition UI Implementation

  Displays available workflow state transitions as buttons based on user role
  and current state. Integrates with the existing WorkflowTransitionModal.

  Features:
  - Shows current state badge prominently
  - Displays available transition buttons
  - Color-coded buttons per transition type
  - Loading state with disabled buttons
  - Error message display
  - Reason required indicator for specific transitions
  - Full i18n support (EN/NL)
  - Accessible with ARIA attributes
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import type { WorkflowState, UserRole } from '$lib/api/types';
	import WorkflowStateBadge from './WorkflowStateBadge.svelte';

	interface Props {
		/** Current workflow state */
		currentState: WorkflowState;
		/** Array of valid transitions from current state */
		validTransitions: WorkflowState[];
		/** Current user's role */
		userRole: UserRole;
		/** Callback when a transition button is clicked */
		onTransitionClick: (targetState: WorkflowState) => void;
		/** Loading state - disables all buttons */
		isLoading?: boolean;
		/** Error message to display */
		error?: string | null;
	}

	let {
		currentState,
		validTransitions,
		userRole,
		onTransitionClick,
		isLoading = false,
		error = null
	}: Props = $props();

	/**
	 * States that require a reason to be provided
	 */
	const REASON_REQUIRED_STATES: WorkflowState[] = ['rejected', 'needs_more_research'];

	/**
	 * Get translated workflow state label
	 */
	function getStateLabel(state: WorkflowState): string {
		return $t(`workflow.states.${state}`) || state.replace(/_/g, ' ');
	}

	/**
	 * Get translated workflow state description
	 */
	function getStateDescription(state: WorkflowState): string {
		return $t(`workflow.descriptions.${state}`) || '';
	}

	/**
	 * Check if reason is required for this transition
	 */
	function isReasonRequired(state: WorkflowState): boolean {
		return REASON_REQUIRED_STATES.includes(state);
	}

	/**
	 * Get button color classes based on transition target state
	 */
	function getButtonClasses(state: WorkflowState): string {
		switch (state) {
			// Success transitions - green/emerald
			case 'published':
			case 'corrected':
				return 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-500';

			// Danger transitions - red
			case 'rejected':
				return 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500';

			// Warning/attention - orange
			case 'needs_more_research':
			case 'under_correction':
				return 'bg-orange-600 hover:bg-orange-700 text-white focus:ring-orange-500';

			// Review states - purple
			case 'admin_review':
			case 'peer_review':
			case 'final_approval':
				return 'bg-purple-600 hover:bg-purple-700 text-white focus:ring-purple-500';

			// Active/research states - yellow
			case 'in_research':
			case 'draft_ready':
				return 'bg-yellow-600 hover:bg-yellow-700 text-white focus:ring-yellow-500';

			// Queue/assignment - blue
			case 'queued':
			case 'assigned':
				return 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500';

			// Archive/inactive - gray
			case 'archived':
			case 'duplicate_detected':
				return 'bg-gray-600 hover:bg-gray-700 text-white focus:ring-gray-500';

			// Default - primary color
			default:
				return 'bg-primary-600 hover:bg-primary-700 text-white focus:ring-primary-500';
		}
	}

	/**
	 * Get icon for transition button
	 */
	function getTransitionIcon(state: WorkflowState): string {
		switch (state) {
			case 'published':
				return '✓';
			case 'rejected':
				return '✗';
			case 'in_research':
				return '🔍';
			case 'draft_ready':
				return '📝';
			case 'admin_review':
				return '👔';
			case 'peer_review':
				return '👥';
			case 'final_approval':
				return '✅';
			case 'needs_more_research':
				return '🔎';
			case 'queued':
				return '📋';
			case 'assigned':
				return '👤';
			case 'archived':
				return '📦';
			case 'under_correction':
				return '🔧';
			case 'corrected':
				return '✓';
			default:
				return '→';
		}
	}

	/**
	 * Handle button click
	 */
	function handleClick(state: WorkflowState) {
		if (!isLoading) {
			onTransitionClick(state);
		}
	}
</script>

<div
	role="region"
	aria-label={$t('submissions.transition.validTransitions')}
	data-testid="workflow-transition-panel"
	class="bg-white rounded-lg border border-gray-200 p-4"
>
	<!-- Header with current state -->
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
		<div>
			<h3 class="text-sm font-medium text-gray-500 mb-1">
				{$t('submissions.detail.currentStatus')}
			</h3>
			<WorkflowStateBadge state={currentState} size="md" prominent />
		</div>

		{#if isLoading}
			<div data-testid="loading-indicator" class="flex items-center gap-2 text-gray-500">
				<svg
					class="animate-spin h-4 w-4"
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
				<span class="text-sm">{$t('submissions.transition.confirming')}</span>
			</div>
		{/if}
	</div>

	<!-- Error message -->
	{#if error}
		<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
			<p class="text-sm text-red-700">{error}</p>
		</div>
	{/if}

	<!-- Transitions section -->
	<div>
		<h4 class="text-sm font-medium text-gray-700 mb-3">
			{$t('submissions.transition.validTransitions')}
		</h4>

		{#if validTransitions.length === 0}
			<p class="text-sm text-gray-500 italic">
				{$t('submissions.transition.noTransitions')}
			</p>
		{:else}
			<div class="flex flex-wrap gap-2">
				{#each validTransitions as targetState}
					<button
						type="button"
						onclick={() => handleClick(targetState)}
						disabled={isLoading}
						title={getStateDescription(targetState)}
						class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed {getButtonClasses(
							targetState
						)}"
					>
						<span aria-hidden="true">{getTransitionIcon(targetState)}</span>
						<span>{getStateLabel(targetState)}</span>
						{#if isReasonRequired(targetState)}
							<span class="text-xs opacity-75" title={$t('submissions.transition.reason')}>✱</span>
						{/if}
					</button>
				{/each}
			</div>

			<!-- Reason required note -->
			{#if validTransitions.some((s) => isReasonRequired(s))}
				<p class="mt-3 text-xs text-gray-500">
					<span class="font-medium">✱</span>
					{$t('submissions.transition.reasonRequired') || 'Reason required'}
				</p>
			{/if}
		{/if}
	</div>
</div>
