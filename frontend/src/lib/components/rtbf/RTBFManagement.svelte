<!--
  RTBF Management Component

  Issue #92: Backend: Right to be Forgotten Workflow (TDD)
  EPIC #53: GDPR & Data Retention Compliance

  Admin dashboard for managing GDPR deletion requests
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import { onMount } from 'svelte';
	import { getAllRTBFRequests, processRTBFRequest, rejectRTBFRequest } from '$lib/api/rtbf';
	import type { RTBFRequest, RTBFRequestStatus } from '$lib/api/types';

	let requests = $state<RTBFRequest[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let statusFilter = $state<RTBFRequestStatus | 'all'>('all');
	let pendingCount = $state(0);
	let processingCount = $state(0);

	// Load requests
	async function loadRequests() {
		isLoading = true;
		error = null;

		try {
			const params = statusFilter !== 'all' ? { status: statusFilter } : {};
			const response = await getAllRTBFRequests(params);
			requests = response.items;
			pendingCount = response.pending_count;
			processingCount = response.processing_count;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load requests';
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadRequests();
	});

	// Watch filter changes
	$effect(() => {
		if (statusFilter) {
			loadRequests();
		}
	});

	// Process a request
	async function handleProcess(requestId: string) {
		if (!confirm($t('rtbf.admin.processConfirm'))) {
			return;
		}

		try {
			await processRTBFRequest(requestId);
			alert($t('rtbf.admin.processSuccess'));
			await loadRequests();
		} catch (err) {
			alert($t('rtbf.admin.processError'));
		}
	}

	// Reject a request
	async function handleReject(requestId: string) {
		const reason = prompt($t('rtbf.admin.rejectReason'));
		if (!reason) return;

		try {
			await rejectRTBFRequest(requestId, reason);
			alert($t('rtbf.admin.rejectSuccess'));
			await loadRequests();
		} catch (err) {
			alert($t('rtbf.admin.rejectError'));
		}
	}

	// Format date
	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString();
	}

	// Get status badge color
	function getStatusColor(status: RTBFRequestStatus): string {
		switch (status) {
			case 'pending':
				return 'bg-yellow-100 text-yellow-800';
			case 'processing':
				return 'bg-blue-100 text-blue-800';
			case 'completed':
				return 'bg-green-100 text-green-800';
			case 'rejected':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<div class="bg-white shadow rounded-lg">
	<!-- Header -->
	<div class="px-6 py-4 border-b border-gray-200">
		<h1 class="text-2xl font-bold text-gray-900">{$t('rtbf.admin.title')}</h1>
		<p class="mt-1 text-sm text-gray-600">{$t('rtbf.admin.description')}</p>
	</div>

	<!-- Filter Tabs -->
	<div class="border-b border-gray-200">
		<nav class="flex -mb-px">
			<button
				onclick={() => (statusFilter = 'all')}
				class="px-6 py-3 text-sm font-medium border-b-2 {statusFilter === 'all'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				{$t('rtbf.admin.filterAll')}
			</button>
			<button
				onclick={() => (statusFilter = 'pending')}
				class="px-6 py-3 text-sm font-medium border-b-2 {statusFilter === 'pending'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				{$t('rtbf.admin.filterPending')}
				{#if pendingCount > 0}
					<span class="ml-2 px-2 py-0.5 rounded-full text-xs bg-yellow-100 text-yellow-800">
						{pendingCount}
					</span>
				{/if}
			</button>
			<button
				onclick={() => (statusFilter = 'processing')}
				class="px-6 py-3 text-sm font-medium border-b-2 {statusFilter === 'processing'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				{$t('rtbf.admin.filterProcessing')}
				{#if processingCount > 0}
					<span class="ml-2 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-800">
						{processingCount}
					</span>
				{/if}
			</button>
			<button
				onclick={() => (statusFilter = 'completed')}
				class="px-6 py-3 text-sm font-medium border-b-2 {statusFilter === 'completed'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				{$t('rtbf.admin.filterCompleted')}
			</button>
			<button
				onclick={() => (statusFilter = 'rejected')}
				class="px-6 py-3 text-sm font-medium border-b-2 {statusFilter === 'rejected'
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				{$t('rtbf.admin.filterRejected')}
			</button>
		</nav>
	</div>

	<!-- Content -->
	<div class="p-6">
		{#if isLoading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
				<span class="ml-3 text-gray-600">{$t('common.loading')}</span>
			</div>
		{:else if error}
			<div class="bg-red-50 border border-red-200 rounded-md p-4">
				<p class="text-sm text-red-800">{error}</p>
			</div>
		{:else if requests.length === 0}
			<div class="text-center py-12">
				<p class="text-gray-500">{$t('rtbf.admin.noPending')}</p>
			</div>
		{:else}
			<!-- Requests Table -->
			<div class="overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								{$t('rtbf.admin.user')}
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								{$t('rtbf.admin.reason')}
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								{$t('rtbf.admin.requestedAt')}
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								{$t('rtbf.admin.status')}
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								{$t('rtbf.admin.actions')}
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each requests as request}
							<tr>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm font-medium text-gray-900">
										{request.notification_email || request.user_id}
									</div>
								</td>
								<td class="px-6 py-4">
									<div class="text-sm text-gray-900 max-w-xs truncate">{request.reason}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-500">{formatDate(request.created_at)}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span
										class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full {getStatusColor(
											request.status
										)}"
									>
										{$t(`rtbf.status.${request.status}`)}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
									{#if request.status === 'pending'}
										<button
											onclick={() => handleProcess(request.id)}
											class="text-green-600 hover:text-green-900 mr-4"
										>
											{$t('rtbf.admin.process')}
										</button>
										<button
											onclick={() => handleReject(request.id)}
											class="text-red-600 hover:text-red-900"
										>
											{$t('rtbf.admin.reject')}
										</button>
									{:else if request.status === 'rejected' && request.rejection_reason}
										<span class="text-gray-500 text-xs">{request.rejection_reason}</span>
									{:else if request.status === 'completed' && request.deletion_summary}
										<span class="text-gray-500 text-xs">
											Deleted: {Object.values(request.deletion_summary).reduce((a, b) => a + b, 0)} items
										</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>
