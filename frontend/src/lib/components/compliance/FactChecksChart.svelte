<!--
  FactChecksChart component - Bar chart showing monthly fact-check counts.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { t } from 'svelte-i18n';
	import type { MonthlyFactCheckCountResponse } from '$lib/api/types';

	interface Props {
		data: MonthlyFactCheckCountResponse | null;
		loading?: boolean;
		error?: string | null;
	}

	let { data, loading = false, error = null }: Props = $props();

	let canvas: HTMLCanvasElement;
	let chart: any = null;

	// Calculate months below EFCSN minimum
	const monthsBelowMinimum = $derived(
		data?.months.filter((m) => !m.meets_efcsn_minimum).length ?? 0
	);

	// Format month label
	function formatMonth(year: number, month: number): string {
		const date = new Date(year, month - 1);
		return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
	}

	// Create or update chart
	async function createChart() {
		if (!canvas || !data) return;

		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		// Dynamically import Chart.js
		const { Chart, registerables } = await import('chart.js');
		Chart.register(...registerables);

		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}

		const labels = data.months.map((m) => formatMonth(m.year, m.month));
		const values = data.months.map((m) => m.count);
		const colors = data.months.map((m) =>
			m.meets_efcsn_minimum ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'
		);

		chart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels,
				datasets: [
					{
						label: 'Fact-Checks',
						data: values,
						backgroundColor: colors,
						borderColor: colors.map((c) => c.replace('0.8', '1')),
						borderWidth: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						display: false
					},
					tooltip: {
						callbacks: {
							afterLabel: (context) => {
								const monthData = data?.months[context.dataIndex];
								return monthData?.meets_efcsn_minimum
									? 'Meets EFCSN minimum'
									: 'Below EFCSN minimum (4)';
							}
						}
					}
				},
				scales: {
					y: {
						beginAtZero: true,
						ticks: {
							stepSize: 1
						}
					}
				}
			}
		});
	}

	onMount(() => {
		if (data) {
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
		if (data && canvas) {
			createChart();
		}
	});
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
	<div class="flex items-center justify-between mb-4">
		<h2 class="text-xl font-semibold text-gray-900">
			{$t('compliance.factChecksChart.title')}
		</h2>
		<div class="text-sm text-blue-600 flex items-center">
			<span class="w-3 h-0.5 bg-blue-400 mr-2"></span>
			{$t('compliance.factChecksChart.efcsnMinimum')}
		</div>
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
	{:else if data}
		<!-- Summary Stats -->
		<div class="grid grid-cols-3 gap-4 mb-6">
			<div class="text-center">
				<div class="text-sm text-gray-500">{$t('compliance.factChecksChart.total')}</div>
				<div class="text-2xl font-bold text-gray-900">{data.total_count}</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-500">{$t('compliance.factChecksChart.average')}</div>
				<div class="text-2xl font-bold text-gray-900">{data.average_per_month}</div>
			</div>
			<div class="text-center">
				<div class="text-sm text-gray-500">Below Minimum</div>
				<div
					class="text-2xl font-bold {monthsBelowMinimum > 0 ? 'text-red-600' : 'text-green-600'}"
					data-testid="months-below-minimum"
				>
					{monthsBelowMinimum}
				</div>
			</div>
		</div>

		<!-- Chart -->
		<div
			class="h-64"
			role="img"
			aria-label="Fact-checks per month bar chart showing publication counts"
		>
			<canvas bind:this={canvas}></canvas>
		</div>
	{/if}
</div>
