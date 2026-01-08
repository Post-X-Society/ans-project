<!--
  TimeToPublicationCard component - Displays time-to-publication metrics.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { TimeToPublicationMetrics } from '$lib/api/types';

	interface Props {
		metrics: TimeToPublicationMetrics | null;
		loading?: boolean;
		error?: string | null;
	}

	let { metrics, loading = false, error = null }: Props = $props();
</script>

<div
	class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
	role="region"
	aria-label="Time to Publication metrics"
>
	<h2 class="text-xl font-semibold text-gray-900 mb-4">
		{$t('compliance.timeToPublication.title')}
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
		<!-- Main Metric -->
		<div class="text-center mb-6 pb-4 border-b border-gray-200">
			<div class="text-4xl font-bold text-primary-600">
				{metrics.average_hours.toFixed(1)}
			</div>
			<div class="text-sm text-gray-500">{$t('compliance.timeToPublication.average')} ({$t('compliance.timeToPublication.hours')})</div>
		</div>

		<!-- Secondary Metrics -->
		<div class="grid grid-cols-2 gap-4">
			<div class="bg-gray-50 rounded-lg p-3 text-center">
				<div class="text-2xl font-semibold text-gray-900">
					{Math.round(metrics.median_hours)}
				</div>
				<div class="text-xs text-gray-500">{$t('compliance.timeToPublication.median')}</div>
			</div>

			<div class="bg-gray-50 rounded-lg p-3 text-center">
				<div class="text-2xl font-semibold text-gray-900">
					{metrics.total_published}
				</div>
				<div class="text-xs text-gray-500">{$t('compliance.timeToPublication.totalPublished')}</div>
			</div>

			<div class="bg-gray-50 rounded-lg p-3 text-center">
				<div class="text-2xl font-semibold text-green-600">
					{Math.round(metrics.min_hours)}
				</div>
				<div class="text-xs text-gray-500">{$t('compliance.timeToPublication.min')}</div>
			</div>

			<div class="bg-gray-50 rounded-lg p-3 text-center" data-testid="max-hours">
				<div class="text-2xl font-semibold text-orange-600">
					{Math.round(metrics.max_hours)}
				</div>
				<div class="text-xs text-gray-500">{$t('compliance.timeToPublication.max')}</div>
			</div>
		</div>

		<!-- Performance Indicator -->
		<div class="mt-4 pt-4 border-t border-gray-200">
			<div class="flex items-center justify-between text-sm">
				<span class="text-gray-500">Performance</span>
				{#if metrics.average_hours <= 24}
					<span class="text-green-600 font-medium">Excellent (&lt; 24h)</span>
				{:else if metrics.average_hours <= 48}
					<span class="text-blue-600 font-medium">Good (&lt; 48h)</span>
				{:else if metrics.average_hours <= 72}
					<span class="text-yellow-600 font-medium">Moderate (&lt; 72h)</span>
				{:else}
					<span class="text-orange-600 font-medium">Needs Improvement</span>
				{/if}
			</div>
		</div>
	{/if}
</div>
