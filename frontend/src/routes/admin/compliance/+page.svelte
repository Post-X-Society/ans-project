<!--
  EFCSN Compliance Dashboard page.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { currentUser } from '$lib/stores/auth';
	import { getAnalyticsDashboard } from '$lib/api/analytics';
	import type { AnalyticsDashboardResponse } from '$lib/api/types';
	import type { PageData } from './$types';

	import {
		ComplianceChecklist,
		FactChecksChart,
		TimeToPublicationCard,
		RatingDistributionChart,
		SourceQualityCard,
		CorrectionRateCard
	} from '$lib/components/compliance';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let dashboard = $state<AnalyticsDashboardResponse | null>(data.dashboard);
	let isLoading = $state(false);
	let error = $state<string | null>(data.error);
	let lastRefresh = $state<Date>(new Date());

	const isAdmin = $derived(
		$currentUser?.role === 'admin' || $currentUser?.role === 'super_admin'
	);

	$effect(() => {
		if ($currentUser && !isAdmin) {
			goto('/dashboard');
		}
	});

	async function refreshDashboard() {
		isLoading = true;
		error = null;

		try {
			dashboard = await getAnalyticsDashboard();
			lastRefresh = new Date();
		} catch (err) {
			console.error('Failed to refresh dashboard:', err);
			error = err instanceof Error ? err.message : 'Failed to refresh dashboard';
		} finally {
			isLoading = false;
		}
	}

	function formatLastRefresh(date: Date): string {
		return date.toLocaleTimeString();
	}
</script>

<svelte:head>
	<title>{$t('compliance.dashboard.title')} | Ans</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-7xl">
	<!-- Header -->
	<div class="flex items-center justify-between mb-8">
		<div>
			<h1 class="text-3xl font-bold text-gray-900">
				{$t('compliance.dashboard.title')}
			</h1>
			<p class="text-gray-600 mt-1">
				{$t('compliance.dashboard.description')}
			</p>
		</div>
		<div class="flex items-center gap-4">
			<span class="text-sm text-gray-500">
				{$t('compliance.dashboard.lastRefresh')}: {formatLastRefresh(lastRefresh)}
			</span>
			<button
				type="button"
				onclick={refreshDashboard}
				disabled={isLoading}
				class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition flex items-center gap-2"
			>
				{#if isLoading}
					<svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
					</svg>
				{/if}
				{$t('compliance.dashboard.refresh')}
			</button>
		</div>
	</div>

	{#if error && !dashboard}
		<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
			<p class="text-red-700 mb-4">{error}</p>
			<button
				type="button"
				onclick={refreshDashboard}
				class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
			>
				{$t('common.tryAgain')}
			</button>
		</div>
	{:else}
		<!-- EFCSN Compliance Status - Full Width -->
		<div class="mb-8">
			<ComplianceChecklist
				compliance={dashboard?.efcsn_compliance ?? null}
				loading={isLoading}
				error={error}
			/>
		</div>

		<!-- Charts Row -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<FactChecksChart
				data={dashboard?.monthly_fact_checks ?? null}
				loading={isLoading}
			/>
			<RatingDistributionChart
				data={dashboard?.rating_distribution ?? null}
				loading={isLoading}
			/>
		</div>

		<!-- Metrics Row -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<TimeToPublicationCard
				metrics={dashboard?.time_to_publication ?? null}
				loading={isLoading}
			/>
			<SourceQualityCard
				metrics={dashboard?.source_quality ?? null}
				loading={isLoading}
			/>
			<CorrectionRateCard
				metrics={dashboard?.correction_rate ?? null}
				loading={isLoading}
			/>
		</div>

		<!-- Generated Timestamp -->
		{#if dashboard}
			<div class="text-center text-sm text-gray-500 mt-8">
				{$t('compliance.dashboard.generatedAt')}:
				{new Date(dashboard.generated_at).toLocaleString()}
			</div>
		{/if}
	{/if}
</div>
