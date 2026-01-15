<!--
  WorkflowStateBadge Component

  Issue #179: Workflow Transition UI Implementation

  Displays a prominent, color-coded badge showing the current workflow state.
  Follows EFCSN workflow states with appropriate visual indicators.

  Features:
  - Color-coded states per ADR 0006 requirements
  - Icons for each state category
  - Multiple size variants (sm, md, lg)
  - Prominent mode for header display
  - Full i18n support (EN/NL)
  - Accessible with ARIA attributes
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import type { WorkflowState } from '$lib/api/types';

	interface Props {
		/** The workflow state to display */
		state: WorkflowState;
		/** Size variant: sm (default), md, lg */
		size?: 'sm' | 'md' | 'lg';
		/** Display in prominent mode with larger padding */
		prominent?: boolean;
		/** Make the badge focusable/interactive */
		interactive?: boolean;
	}

	let { state, size = 'sm', prominent = false, interactive = false }: Props = $props();

	/**
	 * Get translated workflow state label
	 */
	function getStateLabel(workflowState: WorkflowState): string {
		return $t(`workflow.states.${workflowState}`) || workflowState.replace(/_/g, ' ');
	}

	/**
	 * Get color classes based on workflow state
	 * Colors follow ADR 0006 specifications
	 */
	function getColorClasses(workflowState: WorkflowState): string {
		switch (workflowState) {
			// Initial/inactive states - gray
			case 'submitted':
			case 'archived':
			case 'duplicate_detected':
				return 'bg-gray-100 text-gray-800 border-gray-200';

			// Queue state - blue
			case 'queued':
			case 'assigned':
				return 'bg-blue-100 text-blue-800 border-blue-200';

			// Active research states - yellow
			case 'in_research':
			case 'draft_ready':
				return 'bg-yellow-100 text-yellow-800 border-yellow-200';

			// Needs attention - orange
			case 'needs_more_research':
			case 'under_correction':
				return 'bg-orange-100 text-orange-800 border-orange-200';

			// Review states - purple
			case 'admin_review':
			case 'peer_review':
			case 'final_approval':
				return 'bg-purple-100 text-purple-800 border-purple-200';

			// Success states - emerald/green
			case 'published':
			case 'corrected':
				return 'bg-emerald-100 text-emerald-800 border-emerald-200';

			// Rejected - red
			case 'rejected':
				return 'bg-red-100 text-red-800 border-red-200';

			default:
				return 'bg-gray-100 text-gray-800 border-gray-200';
		}
	}

	/**
	 * Get icon for each workflow state
	 */
	function getIcon(workflowState: WorkflowState): string {
		switch (workflowState) {
			// Initial states
			case 'submitted':
				return '📥';
			case 'queued':
				return '📋';
			case 'archived':
				return '📦';
			case 'duplicate_detected':
				return '🔄';

			// Active states
			case 'assigned':
				return '👤';
			case 'in_research':
				return '🔍';
			case 'draft_ready':
				return '📝';
			case 'needs_more_research':
				return '🔎';

			// Review states
			case 'admin_review':
				return '👔';
			case 'peer_review':
				return '👥';
			case 'final_approval':
				return '✅';

			// Terminal states
			case 'published':
				return '✓';
			case 'rejected':
				return '✗';

			// Correction states
			case 'under_correction':
				return '🔧';
			case 'corrected':
				return '✓';

			default:
				return '•';
		}
	}

	/**
	 * Get size classes
	 */
	function getSizeClasses(sizeVariant: 'sm' | 'md' | 'lg'): string {
		switch (sizeVariant) {
			case 'sm':
				return 'text-xs';
			case 'md':
				return 'text-sm';
			case 'lg':
				return 'text-base';
			default:
				return 'text-xs';
		}
	}

	/**
	 * Get padding classes based on prominent mode
	 */
	function getPaddingClasses(isProminent: boolean): string {
		return isProminent ? 'px-4 py-2' : 'px-2 py-1';
	}

	// Derived values for the template
	let colorClasses = $derived(getColorClasses(state));
	let sizeClasses = $derived(getSizeClasses(size));
	let paddingClasses = $derived(getPaddingClasses(prominent));
	let icon = $derived(getIcon(state));
	let label = $derived(getStateLabel(state));
	let ariaLabel = $derived(`${$t('workflow.timeline.currentState')}: ${label}`);
</script>

<span
	role="status"
	aria-label={ariaLabel}
	data-testid="workflow-state-badge"
	tabindex={interactive ? 0 : undefined}
	class="inline-flex items-center gap-1.5 font-medium rounded-full border {colorClasses} {sizeClasses} {paddingClasses}"
	class:cursor-pointer={interactive}
	class:focus:ring-2={interactive}
	class:focus:ring-offset-2={interactive}
	class:focus:outline-none={interactive}
>
	<span class="flex-shrink-0" aria-hidden="true">{icon}</span>
	<span>{label}</span>
</span>
