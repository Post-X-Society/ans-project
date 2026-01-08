<!--
  SourceQualityCard component - Displays source quality metrics.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { SourceQualityMetrics } from '$lib/api/types';

	interface Props {
		metrics: SourceQualityMetrics | null;
		loading?: boolean;
		error?: string | null;
	}

	let { metrics, loading = false, error = null }: Props = $props();

	// EFCSN minimum sources per fact-check
	const EFCSN_MINIMUM_SOURCES = 2;

	// Check if meeting EFCSN minimum on average
	const meetsMinimum = $derived(
		metrics ? metrics.average_sources_per_fact_check >= EFCSN_MINIMUM_SOURCES : false
	);

	// Get source type label
	function getSourceTypeLabel(type: string): string {
		return $t(`sources.types.${type}`) || type;
	}

	// Format credibility score as stars
	function formatCredibility(score: number): string {
		const stars = Math.round(score);
		return '★'.repeat(stars) + '☆'.repeat(5 - stars);
	}
</script>

<div
	class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
	role="region"
	aria-label="Source Quality metrics"
>
	<h2 class="text-xl font-semibold text-gray-900 mb-4">
		{$t('compliance.sourceQuality.title')}
	</h2>

	{#if loading}
		<div class="flex items-center justify-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
			<span class="ml-3 text-gray-600">{$t('common.loading')}</span>
		</div>
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
			{error}
		</div>
	{:else if metrics}
		<!-- EFCSN Compliance Indicator -->
		<div class="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
			<span class="text-sm text-gray-500">{$t('compliance.sourceQuality.efcsnMinimum')}</span>
			<span
				class="font-medium {meetsMinimum ? 'text-green-600' : 'text-red-600'}"
				data-testid="source-compliance-indicator"
			>
				{meetsMinimum ? '✓ Compliant' : '✗ Below minimum'}
			</span>
		</div>

		<!-- Main Metrics -->
		<div class="grid grid-cols-2 gap-4 mb-6">
			<div class="bg-gray-50 rounded-lg p-4 text-center">
				<div class="text-3xl font-bold text-primary-600">
					{metrics.average_sources_per_fact_check.toFixed(1)}
				</div>
				<div class="text-xs text-gray-500">{$t('compliance.sourceQuality.avgSources')}</div>
			</div>

			<div class="bg-gray-50 rounded-lg p-4 text-center">
				<div class="text-3xl font-bold text-yellow-500">
					{metrics.average_credibility_score.toFixed(1)}
				</div>
				<div class="text-xs text-gray-500">{$t('compliance.sourceQuality.avgCredibility')}</div>
				<div class="text-yellow-500 text-sm mt-1">
					{formatCredibility(metrics.average_credibility_score)}
				</div>
			</div>
		</div>

		<!-- Secondary Metrics -->
		<div class="grid grid-cols-3 gap-3 mb-6">
			<div class="text-center">
				<div class="text-xl font-semibold text-gray-900">{metrics.total_sources}</div>
				<div class="text-xs text-gray-500">{$t('compliance.sourceQuality.totalSources')}</div>
			</div>
			<div class="text-center">
				<div class="text-xl font-semibold text-green-600">{metrics.fact_checks_meeting_minimum}</div>
				<div class="text-xs text-gray-500">{$t('compliance.sourceQuality.meetingMinimum')}</div>
			</div>
			<div class="text-center">
				<div class="text-xl font-semibold text-red-600">{metrics.fact_checks_below_minimum}</div>
				<div class="text-xs text-gray-500">{$t('compliance.sourceQuality.belowMinimum')}</div>
			</div>
		</div>

		<!-- Sources by Type -->
		{#if Object.keys(metrics.sources_by_type).length > 0}
			<div class="pt-4 border-t border-gray-200">
				<h3 class="text-sm font-medium text-gray-700 mb-3">Sources by Type</h3>
				<div class="space-y-2">
					{#each Object.entries(metrics.sources_by_type) as [type, count]}
						{@const percentage = metrics.total_sources > 0 ? (count / metrics.total_sources) * 100 : 0}
						<div class="flex items-center">
							<span class="text-sm text-gray-600 w-24">{getSourceTypeLabel(type)}</span>
							<div class="flex-1 mx-3">
								<div class="h-2 bg-gray-200 rounded-full overflow-hidden">
									<div
										class="h-full bg-primary-500 rounded-full transition-all"
										style="width: {percentage}%"
									></div>
								</div>
							</div>
							<span class="text-sm font-medium text-gray-900 w-12 text-right">{count}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>
