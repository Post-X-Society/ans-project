<!--
  RatingDistributionChart component - Doughnut chart showing rating distribution.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { t } from 'svelte-i18n';
	import type { RatingDistributionResponse } from '$lib/api/types';

	interface Props {
		data: RatingDistributionResponse | null;
		loading?: boolean;
		error?: string | null;
	}

	let { data, loading = false, error = null }: Props = $props();

	let canvas: HTMLCanvasElement;
	let chart: any = null;

	// Rating colors
	const ratingColors: Record<string, string> = {
		true: '#22c55e', // green-500
		false: '#ef4444', // red-500
		partly_false: '#f97316', // orange-500
		missing_context: '#eab308', // yellow-500
		altered: '#8b5cf6', // violet-500
		satire: '#06b6d4', // cyan-500
		unverifiable: '#6b7280' // gray-500
	};

	// Get translated rating name
	function getRatingName(rating: string): string {
		return $t(`ratings.${rating}.name`) || rating;
	}

	// Create or update chart
	async function createChart() {
		if (!canvas || !data || data.ratings.length === 0) return;

		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		// Dynamically import Chart.js
		const { Chart, registerables } = await import('chart.js');
		Chart.register(...registerables);

		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}

		const labels = data.ratings.map((r) => getRatingName(r.rating));
		const values = data.ratings.map((r) => r.count);
		const colors = data.ratings.map((r) => ratingColors[r.rating] || '#6b7280');

		chart = new Chart(ctx, {
			type: 'doughnut',
			data: {
				labels,
				datasets: [
					{
						data: values,
						backgroundColor: colors,
						borderColor: '#ffffff',
						borderWidth: 2
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'right',
						labels: {
							usePointStyle: true,
							padding: 15
						}
					},
					tooltip: {
						callbacks: {
							label: (context) => {
								const value = context.raw as number;
								const total = data?.total_count || 1;
								const percentage = ((value / total) * 100).toFixed(1);
								return `${context.label}: ${value} (${percentage}%)`;
							}
						}
					}
				}
			}
		});
	}

	onMount(() => {
		if (data && data.ratings.length > 0) {
			createChart();
		}
	});

	onDestroy(() => {
		if (chart) {
			chart.destroy();
		}
	});

	// Recreate chart when data changes
	$effect(() => {
		if (data && canvas && data.ratings.length > 0) {
			createChart();
		}
	});
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
	<div class="flex items-center justify-between mb-4">
		<h2 class="text-xl font-semibold text-gray-900">
			{$t('compliance.ratingDistribution.title')}
		</h2>
		{#if data}
			<div class="text-sm text-gray-500">
				{$t('compliance.ratingDistribution.total')}: <span class="font-semibold">{data.total_count}</span>
			</div>
		{/if}
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
			<span class="ml-3 text-gray-600">{$t('common.loading')}</span>
		</div>
	{:else if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
			{error}
		</div>
	{:else if data && data.ratings.length > 0}
		<!-- Chart -->
		<div
			class="h-64 mb-4"
			role="img"
			aria-label="Rating distribution doughnut chart showing verdict breakdown"
		>
			<canvas bind:this={canvas}></canvas>
		</div>

		<!-- Rating Breakdown -->
		<div class="grid grid-cols-2 gap-2 pt-4 border-t border-gray-200">
			{#each data.ratings as item}
				<div class="flex items-center justify-between px-2 py-1">
					<div class="flex items-center">
						<span
							class="w-3 h-3 rounded-full mr-2"
							style="background-color: {ratingColors[item.rating] || '#6b7280'}"
						></span>
						<span class="text-sm text-gray-700">{getRatingName(item.rating)}</span>
					</div>
					<span class="text-sm font-medium text-gray-900">{Math.round(item.percentage)}%</span>
				</div>
			{/each}
		</div>
	{:else}
		<div class="text-center py-8 text-gray-500">
			<p>{$t('common.noData') || 'No data available'}</p>
		</div>
	{/if}
</div>
