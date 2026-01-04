<!--
  WorkflowTransitionModal Component

  Issue #154: Fix TanStack Query reactivity issue
  Extracted from submissions/[id]/+page.svelte for modularity

  Features:
  - Modal dialog for workflow state transitions
  - Optional reason/notes textarea
  - Loading state during submission
  - Accessible with proper ARIA roles
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import type { WorkflowState } from '$lib/api/types';

	interface Props {
		show: boolean;
		targetState: WorkflowState | null;
		isSubmitting: boolean;
		onConfirm: (reason: string) => void;
		onCancel: () => void;
	}

	let { show, targetState, isSubmitting, onConfirm, onCancel }: Props = $props();

	let reason = $state('');

	/**
	 * Get translated workflow state label
	 */
	function getStateLabel(state: WorkflowState): string {
		return $t(`workflow.states.${state}`) || state;
	}

	/**
	 * Handle confirm click
	 */
	function handleConfirm() {
		onConfirm(reason);
		reason = ''; // Reset for next use
	}

	/**
	 * Handle cancel click
	 */
	function handleCancel() {
		reason = ''; // Reset
		onCancel();
	}
</script>

{#if show && targetState}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		data-testid="workflow-transition-modal"
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
	>
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
			<h3 id="modal-title" class="text-lg font-semibold text-gray-900 mb-4">
				{$t('submissions.transition.title')}
			</h3>

			<p class="text-gray-600 mb-4">
				Transition to: <strong>{getStateLabel(targetState)}</strong>
			</p>

			<div class="mb-4">
				<label for="transition-reason" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('submissions.transition.reason')}
				</label>
				<textarea
					id="transition-reason"
					bind:value={reason}
					rows="3"
					placeholder={$t('submissions.transition.reasonPlaceholder')}
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				></textarea>
			</div>

			<div class="flex gap-3">
				<button
					data-testid="cancel-button"
					onclick={handleCancel}
					class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
				>
					{$t('common.cancel')}
				</button>
				<button
					data-testid="confirm-button"
					onclick={handleConfirm}
					disabled={isSubmitting}
					class="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition"
				>
					{isSubmitting ? $t('submissions.transition.confirming') : $t('submissions.transition.confirm')}
				</button>
			</div>
		</div>
	</div>
{/if}
