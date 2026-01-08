<!--
  CorrectionRateCard component - Displays correction rate metrics.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { CorrectionRateMetrics } from '$lib/api/types';

	interface Props {
		metrics: CorrectionRateMetrics | null;
		loading?: boolean;
		error?: string | null;
	}

	let { metrics, loading = false, error = null }: Props = $props();

	// Format rate as percentage
	function formatRate(rate: number): string {
		return `${Math.round(rate * 100)}%`;
	}

	// Get correction type label
	function getCorrectionTypeLabel(type: string): string {
		return $t(`corrections.types.${type}`) || type;
	}

	// Get health status based on correction rate
	function getHealthStatus(rate: number): { label: string; color: string } {
		if (rate <= 0.1) {
			return { label: 'Excellent', color: 'text-green-600' };
		} else if (rate <= 0.2) {
			return { label: 'Good', color: 'text-blue-600' };
		} else if (rate <= 0.3) {
			return { label: 'Moderate', color: 'text-yellow-600' };
		} else {
			return { label: 'Needs Attention', color: 'text-orange-600' };
		}
	}

	// Compute health status
	const health = $derived(metrics ? getHealthStatus(metrics.correction_rate) : null);
</script>

<div
	class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
	role="region"
	aria-label="Correction Rate metrics"
>
	<h2 class="text-xl font-semibold text-gray-900 mb-4">
		{$t('compliance.correctionRate.title')}
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
	{:else if metrics && health}
		<!-- Main Rate Display -->
		<div class="text-center mb-6 pb-4 border-b border-gray-200">
			<div class="text-4xl font-bold text-primary-600">
				{formatRate(metrics.correction_rate)}
			</div>
			<div class="text-sm text-gray-500">{$t('compliance.correctionRate.rate')}</div>
			<div class="mt-2 text-sm font-medium {health.color}" data-testid="correction-rate-health">
				{health.label}
			</div>
		</div>

		<!-- Fact-Check & Correction Totals -->
		<div class="grid grid-cols-2 gap-4 mb-6">
			<div class="bg-gray-50 rounded-lg p-3 text-center">
				<div class="text-2xl font-bold text-gray-900">{metrics.total_fact_checks}</div>
				<div class="text-xs text-gray-500">{$t('compliance.correctionRate.totalFactChecks')}</div>
			</div>
			<div class="bg-gray-50 rounded-lg p-3 text-center">
				<div class="text-2xl font-bold text-gray-900">{metrics.total_corrections}</div>
				<div class="text-xs text-gray-500">{$t('compliance.correctionRate.totalCorrections')}</div>
			</div>
		</div>

		<!-- Correction Status Breakdown -->
		<div class="grid grid-cols-3 gap-3 mb-6">
			<div class="text-center p-2 bg-green-50 rounded-lg" data-testid="corrections-accepted">
				<div class="text-xl font-semibold text-green-600">{metrics.corrections_accepted}</div>
				<div class="text-xs text-green-700">{$t('compliance.correctionRate.accepted')}</div>
			</div>
			<div class="text-center p-2 bg-red-50 rounded-lg" data-testid="corrections-rejected">
				<div class="text-xl font-semibold text-red-600">{metrics.corrections_rejected}</div>
				<div class="text-xs text-red-700">{$t('compliance.correctionRate.rejected')}</div>
			</div>
			<div class="text-center p-2 bg-yellow-50 rounded-lg" data-testid="corrections-pending">
				<div class="text-xl font-semibold text-yellow-600">{metrics.corrections_pending}</div>
				<div class="text-xs text-yellow-700">{$t('compliance.correctionRate.pending')}</div>
			</div>
		</div>

		<!-- Corrections by Type -->
		{#if Object.keys(metrics.corrections_by_type).length > 0}
			<div class="pt-4 border-t border-gray-200">
				<h3 class="text-sm font-medium text-gray-700 mb-3">Corrections by Type</h3>
				<div class="space-y-2">
					{#each Object.entries(metrics.corrections_by_type) as [type, count]}
						{@const total = metrics.total_corrections || 1}
						{@const percentage = (count / total) * 100}
						<div class="flex items-center">
							<span class="text-sm text-gray-600 w-24 capitalize">
								{getCorrectionTypeLabel(type)}
							</span>
							<div class="flex-1 mx-3">
								<div class="h-2 bg-gray-200 rounded-full overflow-hidden">
									<div
										class="h-full bg-primary-500 rounded-full transition-all"
										style="width: {percentage}%"
									></div>
								</div>
							</div>
							<span class="text-sm font-medium text-gray-900 w-8 text-right">{count}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>
