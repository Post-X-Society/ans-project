<script lang="ts">
	import { t } from '$lib/i18n';
	import type { WorkflowState } from '$lib/api/types';

	interface Props {
		currentState: WorkflowState;
		className?: string;
	}

	let { currentState, className = '' }: Props = $props();

	// Define the main workflow stages in order
	const stages = [
		{ key: 'submitted', states: ['submitted'] },
		{ key: 'queued', states: ['queued', 'duplicate_detected'] },
		{ key: 'assigned', states: ['assigned'] },
		{ key: 'research', states: ['in_research', 'draft_ready', 'needs_more_research'] },
		{ key: 'review', states: ['admin_review', 'peer_review'] },
		{ key: 'approval', states: ['final_approval'] },
		{ key: 'published', states: ['published', 'corrected'] }
	];

	// Special states (not in main flow)
	const terminalStates = ['rejected', 'archived', 'duplicate_detected'];

	// Calculate which stage we're currently in
	let currentStageIndex = $derived(() => {
		const index = stages.findIndex(stage => stage.states.includes(currentState));
		return index >= 0 ? index : 0;
	});

	// Check if current state is terminal (rejected/archived)
	let isTerminal = $derived(terminalStates.includes(currentState));

	// Calculate progress percentage
	let progressPercentage = $derived(() => {
		if (isTerminal) return 100;
		const idx = currentStageIndex();
		return ((idx + 1) / stages.length) * 100;
	});

	function getStageClass(stageIndex: number): string {
		const idx = currentStageIndex();
		if (idx > stageIndex) return 'completed';
		if (idx === stageIndex) return 'active';
		return 'pending';
	}

	function getStageLabel(stageKey: string): string {
		return $t(`workflow.stages.${stageKey}`);
	}

	function getStateColor(): string {
		if (currentState === 'rejected' || currentState === 'archived') return 'bg-red-600';
		if (currentState === 'published' || currentState === 'corrected') return 'bg-green-600';
		if (currentState === 'duplicate_detected') return 'bg-gray-600';
		return 'bg-primary-600';
	}
</script>

<div class="workflow-progress-bar {className}" role="region" aria-label={$t('workflow.progress.label')}>
	<!-- Current State Badge -->
	<div class="flex items-center justify-between mb-4">
		<div>
			<span class="text-sm font-medium text-gray-600">{$t('workflow.progress.currentStage')}:</span>
			<span class="ml-2 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStateColor()} text-white">
				{$t(`workflow.states.${currentState}`)}
			</span>
		</div>
		<div class="text-sm text-gray-500">
			{#if !isTerminal}
				{$t('workflow.progress.step', { values: { current: currentStageIndex() + 1, total: stages.length } })}
			{/if}
		</div>
	</div>

	<!-- Progress Bar -->
	<div class="relative">
		<!-- Background track -->
		<div class="absolute top-1/2 left-0 right-0 h-1 bg-gray-200 -translate-y-1/2"></div>

		<!-- Progress fill -->
		<div
			class="absolute top-1/2 left-0 h-1 {getStateColor()} -translate-y-1/2 transition-all duration-500"
			style="width: {progressPercentage()}%"
		></div>

		<!-- Stage markers -->
		<div class="relative flex justify-between">
			{#each stages as stage, index}
				{@const stageClass = getStageClass(index)}
				<div class="flex flex-col items-center">
					<!-- Circle marker -->
					<div
						class="w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all z-10
							{stageClass === 'completed' ? 'bg-primary-600 border-primary-600' : ''}
							{stageClass === 'active' ? 'bg-white border-primary-600 ring-4 ring-primary-100' : ''}
							{stageClass === 'pending' ? 'bg-white border-gray-300' : ''}"
					>
						{#if stageClass === 'completed'}
							<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
							</svg>
						{:else if stageClass === 'active'}
							<div class="w-3 h-3 rounded-full bg-primary-600"></div>
						{:else}
							<div class="w-2 h-2 rounded-full bg-gray-300"></div>
						{/if}
					</div>

					<!-- Label -->
					<div class="mt-2 text-xs text-center max-w-[80px]">
						<span
							class="font-medium
								{stageClass === 'completed' || stageClass === 'active' ? 'text-gray-900' : 'text-gray-400'}"
						>
							{getStageLabel(stage.key)}
						</span>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- State Description -->
	<div class="mt-4 text-sm text-gray-600">
		{$t(`workflow.descriptions.${currentState}`)}
	</div>
</div>

<style>
	.workflow-progress-bar {
		padding: 1.5rem;
		background: white;
		border-radius: 0.5rem;
		border: 1px solid #e5e7eb;
	}
</style>
