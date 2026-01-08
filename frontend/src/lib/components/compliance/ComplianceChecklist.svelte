<!--
  ComplianceChecklist component - Displays EFCSN compliance status and checklist.

  Issue #90: Frontend EFCSN Compliance Dashboard (TDD)
  EPIC #52: Analytics & Compliance Dashboard
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { EFCSNComplianceResponse, EFCSNComplianceStatus } from '$lib/api/types';

	interface Props {
		compliance: EFCSNComplianceResponse | null;
		loading?: boolean;
		error?: string | null;
	}

	let { compliance, loading = false, error = null }: Props = $props();

	// Get status color class
	function getStatusColorClass(status: EFCSNComplianceStatus): string {
		switch (status) {
			case 'compliant':
				return 'bg-green-100 text-green-800 border-green-200';
			case 'non_compliant':
				return 'bg-red-100 text-red-800 border-red-200';
			case 'warning':
				return 'bg-yellow-100 text-yellow-800 border-yellow-200';
			case 'at_risk':
				return 'bg-orange-100 text-orange-800 border-orange-200';
			default:
				return 'bg-gray-100 text-gray-800 border-gray-200';
		}
	}

	// Get status icon
	function getStatusIcon(status: EFCSNComplianceStatus): string {
		switch (status) {
			case 'compliant':
				return '✓';
			case 'non_compliant':
				return '✗';
			case 'warning':
				return '⚠';
			case 'at_risk':
				return '!';
			default:
				return '?';
		}
	}

	// Format score color
	function getScoreColor(score: number): string {
		if (score >= 80) return 'text-green-600';
		if (score >= 60) return 'text-yellow-600';
		return 'text-red-600';
	}
</script>

<div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
	<h2 class="text-xl font-semibold text-gray-900 mb-4">
		{$t('compliance.title')}
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
	{:else if compliance}
		<!-- Overall Status and Score -->
		<div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
			<div>
				<span class="text-sm text-gray-500">{$t('compliance.overallStatus')}</span>
				<div
					class="mt-1 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStatusColorClass(
						compliance.overall_status
					)}"
				>
					<span class="mr-1">{getStatusIcon(compliance.overall_status)}</span>
					{$t(`compliance.status.${compliance.overall_status}`)}
				</div>
			</div>
			<div class="text-right">
				<span class="text-sm text-gray-500">{$t('compliance.complianceScore')}</span>
				<div class="text-3xl font-bold {getScoreColor(compliance.compliance_score)}">
					{compliance.compliance_score}%
				</div>
			</div>
		</div>

		<!-- Checklist -->
		<div>
			<h3 class="text-sm font-medium text-gray-700 mb-3">{$t('compliance.checklist')}</h3>
			<ul class="space-y-3" role="list" aria-label="EFCSN compliance checklist">
				{#each compliance.checklist as item}
					<li
						class="flex items-start p-3 rounded-lg border {getStatusColorClass(item.status)}"
						data-testid="status-{item.status}"
					>
						<span
							class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold mr-3"
						>
							{getStatusIcon(item.status)}
						</span>
						<div class="flex-1 min-w-0">
							<div class="flex items-center justify-between">
								<span class="font-medium">{item.requirement}</span>
								{#if item.value && item.threshold}
									<span class="text-sm font-mono">
										{item.value} / {item.threshold}
									</span>
								{/if}
							</div>
							<p class="text-sm mt-1 opacity-80">{item.details}</p>
						</div>
					</li>
				{/each}
			</ul>
		</div>

		<!-- Last Checked -->
		<div class="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-500">
			{$t('compliance.lastChecked')}:
			{new Date(compliance.last_checked).toLocaleString()}
		</div>
	{/if}
</div>
