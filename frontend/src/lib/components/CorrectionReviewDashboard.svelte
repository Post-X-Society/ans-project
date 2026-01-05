<!--
  CorrectionReviewDashboard Component
  Issue #80: Frontend Admin Correction Review Dashboard (TDD)
  EPIC #50: Corrections & Complaints System

  Admin dashboard for reviewing and managing correction requests.
  Features:
  - List pending corrections with SLA countdown
  - Review form (accept/reject)
  - Side-by-side fact-check comparison
  - Apply correction UI
-->
<script lang="ts">
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { t } from 'svelte-i18n';
	import {
		pendingCorrectionsQueryOptions,
		acceptCorrectionMutationOptions,
		rejectCorrectionMutationOptions,
		applyCorrectionMutationOptions
	} from '$lib/api/queries';
	import type { CorrectionResponse, CorrectionType } from '$lib/api/types';

	interface Props {
		onReviewComplete?: () => void;
	}

	let { onReviewComplete }: Props = $props();

	const queryClient = useQueryClient();

	// State
	let selectedCorrection = $state<CorrectionResponse | null>(null);
	let showReviewModal = $state(false);
	let showApplyModal = $state(false);
	let showDetailsPanel = $state(false);
	let resolutionNotes = $state('');
	let changesSummary = $state('');
	let resolutionError = $state('');
	let changesError = $state('');
	let activeFilter = $state<CorrectionType | 'all'>('all');
	let successMessage = $state('');
	let errorMessage = $state('');

	// Query for pending corrections
	const pendingQuery = createQuery(() => pendingCorrectionsQueryOptions());

	// Mutations
	const acceptMutation = createMutation(() => ({
		...acceptCorrectionMutationOptions(),
		onSuccess: () => {
			successMessage = $t('corrections.admin.success.accepted');
			closeReviewModal();
			queryClient.invalidateQueries({ queryKey: ['corrections'] });
			onReviewComplete?.();
		},
		onError: () => {
			errorMessage = $t('corrections.admin.error.acceptFailed');
		}
	}));

	const rejectMutation = createMutation(() => ({
		...rejectCorrectionMutationOptions(),
		onSuccess: () => {
			successMessage = $t('corrections.admin.success.rejected');
			closeReviewModal();
			queryClient.invalidateQueries({ queryKey: ['corrections'] });
			onReviewComplete?.();
		},
		onError: () => {
			errorMessage = $t('corrections.admin.error.rejectFailed');
		}
	}));

	const applyMutation = createMutation(() => ({
		...applyCorrectionMutationOptions(),
		onSuccess: () => {
			successMessage = $t('corrections.admin.success.applied');
			closeApplyModal();
			queryClient.invalidateQueries({ queryKey: ['corrections'] });
			onReviewComplete?.();
		},
		onError: () => {
			errorMessage = $t('corrections.admin.error.applyFailed');
		}
	}));

	// Derived states
	let filteredCorrections = $derived.by(() => {
		if (!pendingQuery.data?.corrections) return [];
		if (activeFilter === 'all') return pendingQuery.data.corrections;
		return pendingQuery.data.corrections.filter((c) => c.correction_type === activeFilter);
	});

	let isReviewing = $derived(acceptMutation.isPending || rejectMutation.isPending);
	let isApplying = $derived(applyMutation.isPending);

	// Helper functions
	function getCorrectionTypeLabel(type: CorrectionType): string {
		switch (type) {
			case 'substantial':
				return $t('corrections.types.substantial');
			case 'update':
				return $t('corrections.types.update');
			case 'minor':
				return $t('corrections.types.minor');
		}
	}

	function getSlaStatus(deadline: string | undefined): {
		text: string;
		isOverdue: boolean;
		daysRemaining: number;
		colorClass: string;
	} {
		if (!deadline) {
			return { text: '', isOverdue: false, daysRemaining: 0, colorClass: 'bg-gray-500' };
		}

		const now = new Date();
		const slaDate = new Date(deadline);
		const diffTime = slaDate.getTime() - now.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays < 0) {
			const overdueDays = Math.abs(diffDays);
			return {
				text:
					overdueDays === 1
						? $t('corrections.admin.sla.dayOverdue')
						: $t('corrections.admin.sla.daysOverdue', { values: { days: overdueDays } }),
				isOverdue: true,
				daysRemaining: diffDays,
				colorClass: 'bg-red-500'
			};
		} else if (diffDays === 0) {
			return {
				text: $t('corrections.admin.sla.dueToday'),
				isOverdue: false,
				daysRemaining: 0,
				colorClass: 'bg-yellow-500'
			};
		} else if (diffDays <= 3) {
			return {
				text:
					diffDays === 1
						? $t('corrections.admin.sla.dayRemaining')
						: $t('corrections.admin.sla.daysRemaining', { values: { days: diffDays } }),
				isOverdue: false,
				daysRemaining: diffDays,
				colorClass: 'bg-yellow-500'
			};
		} else {
			return {
				text: $t('corrections.admin.sla.daysRemaining', { values: { days: diffDays } }),
				isOverdue: false,
				daysRemaining: diffDays,
				colorClass: 'bg-green-500'
			};
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// Modal handlers
	function openReviewModal(correction: CorrectionResponse) {
		selectedCorrection = correction;
		resolutionNotes = '';
		resolutionError = '';
		showReviewModal = true;
	}

	function closeReviewModal() {
		showReviewModal = false;
		selectedCorrection = null;
		resolutionNotes = '';
		resolutionError = '';
	}

	function openApplyModal(correction: CorrectionResponse) {
		selectedCorrection = correction;
		changesSummary = '';
		changesError = '';
		showApplyModal = true;
	}

	function closeApplyModal() {
		showApplyModal = false;
		selectedCorrection = null;
		changesSummary = '';
		changesError = '';
	}

	function openDetailsPanel(correction: CorrectionResponse) {
		selectedCorrection = correction;
		showDetailsPanel = true;
	}

	function closeDetailsPanel() {
		showDetailsPanel = false;
		selectedCorrection = null;
	}

	// Action handlers
	function validateResolutionNotes(): boolean {
		if (resolutionNotes.trim().length < 10) {
			resolutionError = $t('corrections.admin.reviewModal.resolutionNotesMinLength');
			return false;
		}
		resolutionError = '';
		return true;
	}

	function validateChangesSummary(): boolean {
		if (changesSummary.trim().length < 10) {
			changesError = $t('corrections.admin.applyModal.changesSummaryMinLength');
			return false;
		}
		changesError = '';
		return true;
	}

	function handleAccept() {
		if (!selectedCorrection || !validateResolutionNotes()) return;

		acceptMutation.mutate({
			correctionId: selectedCorrection.id,
			data: { resolution_notes: resolutionNotes.trim() }
		});
	}

	function handleReject() {
		if (!selectedCorrection || !validateResolutionNotes()) return;

		rejectMutation.mutate({
			correctionId: selectedCorrection.id,
			data: { resolution_notes: resolutionNotes.trim() }
		});
	}

	function handleApply() {
		if (!selectedCorrection || !validateChangesSummary()) return;

		applyMutation.mutate({
			correctionId: selectedCorrection.id,
			data: {
				changes: { correction_notice: changesSummary.trim() },
				changes_summary: changesSummary.trim()
			}
		});
	}

	function handleRetry() {
		queryClient.invalidateQueries({ queryKey: ['corrections', 'pending'] });
	}

	// Keyboard handler for modals
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			if (showReviewModal) closeReviewModal();
			if (showApplyModal) closeApplyModal();
			if (showDetailsPanel) closeDetailsPanel();
		}
	}

	// Clear messages after timeout
	$effect(() => {
		if (successMessage || errorMessage) {
			const timer = setTimeout(() => {
				successMessage = '';
				errorMessage = '';
			}, 5000);
			return () => clearTimeout(timer);
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="min-h-screen bg-gray-50 p-6">
	<!-- Header -->
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-gray-900">
			{$t('corrections.admin.dashboardTitle')}
		</h1>

		{#if pendingQuery.data}
			<div class="mt-2 flex items-center gap-4">
				<span class="rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
					{$t('corrections.admin.pendingCount', {
						values: { count: pendingQuery.data.total_count }
					})}
				</span>
				{#if pendingQuery.data.overdue_count > 0}
					<span class="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800">
						{$t('corrections.admin.overdueCount', {
							values: { count: pendingQuery.data.overdue_count }
						})}
					</span>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Success/Error Messages -->
	{#if successMessage}
		<div class="mb-4 rounded-md bg-green-50 p-4 text-green-800" role="alert">
			{successMessage}
		</div>
	{/if}

	{#if errorMessage}
		<div class="mb-4 rounded-md bg-red-50 p-4 text-red-800" role="alert">
			{errorMessage}
		</div>
	{/if}

	<!-- Filter Tabs -->
	<div class="mb-6" role="tablist" aria-label="Filter corrections by type">
		<div class="flex gap-2">
			<button
				role="tab"
				aria-selected={activeFilter === 'all'}
				class="rounded-md px-4 py-2 text-sm font-medium transition-colors {activeFilter === 'all'
					? 'bg-blue-600 text-white'
					: 'bg-white text-gray-700 hover:bg-gray-100'}"
				onclick={() => (activeFilter = 'all')}
			>
				{$t('corrections.admin.filterAll')}
			</button>
			<button
				role="tab"
				aria-selected={activeFilter === 'substantial'}
				class="rounded-md px-4 py-2 text-sm font-medium transition-colors {activeFilter ===
				'substantial'
					? 'bg-blue-600 text-white'
					: 'bg-white text-gray-700 hover:bg-gray-100'}"
				onclick={() => (activeFilter = 'substantial')}
			>
				{$t('corrections.admin.filterSubstantial')}
			</button>
			<button
				role="tab"
				aria-selected={activeFilter === 'update'}
				class="rounded-md px-4 py-2 text-sm font-medium transition-colors {activeFilter ===
				'update'
					? 'bg-blue-600 text-white'
					: 'bg-white text-gray-700 hover:bg-gray-100'}"
				onclick={() => (activeFilter = 'update')}
			>
				{$t('corrections.admin.filterUpdate')}
			</button>
			<button
				role="tab"
				aria-selected={activeFilter === 'minor'}
				class="rounded-md px-4 py-2 text-sm font-medium transition-colors {activeFilter ===
				'minor'
					? 'bg-blue-600 text-white'
					: 'bg-white text-gray-700 hover:bg-gray-100'}"
				onclick={() => (activeFilter = 'minor')}
			>
				{$t('corrections.admin.filterMinor')}
			</button>
		</div>
	</div>

	<!-- Loading State -->
	{#if pendingQuery.isPending}
		<div class="py-12 text-center">
			<div
				class="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"
			></div>
			<p class="mt-4 text-gray-600">{$t('corrections.admin.loading')}</p>
		</div>
	{/if}

	<!-- Error State -->
	{#if pendingQuery.isError}
		<div class="rounded-lg bg-red-50 p-8 text-center">
			<p class="text-red-800">{$t('corrections.admin.loadFailed')}</p>
			<button
				onclick={handleRetry}
				class="mt-4 rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
			>
				{$t('corrections.admin.retry')}
			</button>
		</div>
	{/if}

	<!-- Empty State -->
	{#if pendingQuery.isSuccess && filteredCorrections.length === 0}
		<div class="rounded-lg bg-white p-12 text-center shadow-sm">
			<svg
				class="mx-auto h-12 w-12 text-gray-400"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<p class="mt-4 text-lg font-medium text-gray-900">{$t('corrections.admin.noPending')}</p>
			<p class="mt-2 text-gray-600">{$t('corrections.admin.noPendingDescription')}</p>
		</div>
	{/if}

	<!-- Corrections List -->
	{#if pendingQuery.isSuccess && filteredCorrections.length > 0}
		<ul
			class="space-y-4"
			role="list"
			aria-label={$t('corrections.admin.listAriaLabel')}
		>
			{#each filteredCorrections as correction (correction.id)}
				{@const slaStatus = getSlaStatus(correction.sla_deadline)}
				<li
					data-testid="correction-item"
					class="rounded-lg border bg-white p-6 shadow-sm transition-shadow hover:shadow-md {slaStatus.isOverdue
						? 'border-red-500'
						: 'border-gray-200'}"
				>
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<!-- Correction Type Badge -->
							<div class="flex items-center gap-3">
								<span
									class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {correction.correction_type ===
									'substantial'
										? 'bg-red-100 text-red-800'
										: correction.correction_type === 'update'
											? 'bg-yellow-100 text-yellow-800'
											: 'bg-gray-100 text-gray-800'}"
								>
									{getCorrectionTypeLabel(correction.correction_type)}
								</span>
								<!-- SLA Indicator -->
								<span class="flex items-center gap-1 text-sm">
									<span class="sla-indicator h-2 w-2 rounded-full {slaStatus.colorClass}"></span>
									<span class={slaStatus.isOverdue ? 'font-medium text-red-600' : 'text-gray-600'}>
										{slaStatus.text}
									</span>
								</span>
							</div>

							<!-- Request Details -->
							<p class="mt-3 text-gray-900">{correction.request_details}</p>

							<!-- Meta Info -->
							<div class="mt-3 flex flex-wrap items-center gap-4 text-sm text-gray-500">
								<span>
									{$t('corrections.admin.submittedAt', {
										values: { date: formatDate(correction.created_at) }
									})}
								</span>
								{#if correction.requester_email}
									<span>
										{$t('corrections.admin.requesterEmail', {
											values: { email: correction.requester_email }
										})}
									</span>
								{:else}
									<span class="italic">{$t('corrections.admin.noEmail')}</span>
								{/if}
							</div>
						</div>

						<!-- Actions -->
						<div class="ml-4 flex flex-col gap-2">
							{#if correction.status === 'pending'}
								<button
									onclick={() => openReviewModal(correction)}
									aria-label="{$t('corrections.admin.actions.review')} - {correction.id}"
									class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
								>
									{$t('corrections.admin.actions.review')}
								</button>
							{:else if correction.status === 'accepted'}
								<button
									onclick={() => openApplyModal(correction)}
									class="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
								>
									{$t('corrections.admin.actions.applyCorrection')}
								</button>
							{/if}
							<button
								onclick={() => openDetailsPanel(correction)}
								class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
							>
								{$t('corrections.admin.actions.viewDetails')}
							</button>
						</div>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<!-- Review Modal -->
{#if showReviewModal && selectedCorrection}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
		role="dialog"
		aria-labelledby="review-modal-title"
		aria-modal="true"
	>
		<div class="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
			<h2 id="review-modal-title" class="text-xl font-semibold text-gray-900">
				{$t('corrections.admin.reviewModal.title')}
			</h2>

			<div class="mt-4">
				<p class="text-gray-700">{selectedCorrection.request_details}</p>
			</div>

			<div class="mt-4">
				<label for="resolution-notes" class="block text-sm font-medium text-gray-700">
					{$t('corrections.admin.reviewModal.resolutionNotesLabel')}
				</label>
				<textarea
					id="resolution-notes"
					bind:value={resolutionNotes}
					placeholder={$t('corrections.admin.reviewModal.resolutionNotesPlaceholder')}
					rows="4"
					class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
					aria-describedby={resolutionError ? 'resolution-error' : undefined}
				></textarea>
				{#if resolutionError}
					<p id="resolution-error" class="mt-1 text-sm text-red-600">
						{resolutionError}
					</p>
				{/if}
			</div>

			<div class="mt-6 flex justify-end gap-3">
				<button
					onclick={closeReviewModal}
					class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
					disabled={isReviewing}
				>
					{$t('corrections.admin.reviewModal.cancel')}
				</button>
				<button
					onclick={handleReject}
					disabled={isReviewing}
					class="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
				>
					{isReviewing && rejectMutation.isPending
						? $t('corrections.admin.reviewModal.rejecting')
						: $t('corrections.admin.reviewModal.reject')}
				</button>
				<button
					onclick={handleAccept}
					disabled={isReviewing}
					class="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
				>
					{isReviewing && acceptMutation.isPending
						? $t('corrections.admin.reviewModal.accepting')
						: $t('corrections.admin.reviewModal.accept')}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Apply Modal -->
{#if showApplyModal && selectedCorrection}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
		role="dialog"
		aria-labelledby="apply-modal-title"
		aria-modal="true"
	>
		<div class="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
			<h2 id="apply-modal-title" class="text-xl font-semibold text-gray-900">
				{$t('corrections.admin.applyModal.title')}
			</h2>

			<p class="mt-2 text-sm text-gray-600">
				{$t('corrections.admin.applyModal.description')}
			</p>

			<div class="mt-4">
				<label for="changes-summary" class="block text-sm font-medium text-gray-700">
					{$t('corrections.admin.applyModal.changesSummaryLabel')}
				</label>
				<textarea
					id="changes-summary"
					bind:value={changesSummary}
					placeholder={$t('corrections.admin.applyModal.changesSummaryPlaceholder')}
					rows="4"
					class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
					aria-describedby={changesError ? 'changes-error' : undefined}
				></textarea>
				{#if changesError}
					<p id="changes-error" class="mt-1 text-sm text-red-600">
						{changesError}
					</p>
				{/if}
			</div>

			<div class="mt-6 flex justify-end gap-3">
				<button
					onclick={closeApplyModal}
					class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
					disabled={isApplying}
				>
					{$t('corrections.admin.applyModal.cancel')}
				</button>
				<button
					onclick={handleApply}
					disabled={isApplying}
					class="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
				>
					{isApplying
						? $t('corrections.admin.applyModal.applying')
						: $t('corrections.admin.actions.confirmApply')}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Details Panel -->
{#if showDetailsPanel && selectedCorrection}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
		role="dialog"
		aria-labelledby="details-panel-title"
		aria-modal="true"
	>
		<div class="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
			<div class="flex items-start justify-between">
				<h2 id="details-panel-title" class="text-xl font-semibold text-gray-900">
					{$t('corrections.admin.detailsPanel.originalRequest')}
				</h2>
				<button
					onclick={closeDetailsPanel}
					class="text-gray-400 hover:text-gray-600"
					aria-label={$t('corrections.admin.detailsPanel.close')}
				>
					<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<dl class="mt-6 space-y-4">
				<div>
					<dt class="text-sm font-medium text-gray-500">
						{$t('corrections.admin.detailsPanel.correctionType')}
					</dt>
					<dd class="mt-1 text-gray-900">
						{getCorrectionTypeLabel(selectedCorrection.correction_type)}
					</dd>
				</div>

				<div>
					<dt class="text-sm font-medium text-gray-500">
						{$t('corrections.admin.detailsPanel.requestDetails')}
					</dt>
					<dd class="mt-1 text-gray-900">{selectedCorrection.request_details}</dd>
				</div>

				<div>
					<dt class="text-sm font-medium text-gray-500">
						{$t('corrections.admin.detailsPanel.requester')}
					</dt>
					<dd class="mt-1 text-gray-900">
						{selectedCorrection.requester_email || $t('corrections.admin.noEmail')}
					</dd>
				</div>

				<div>
					<dt class="text-sm font-medium text-gray-500">
						{$t('corrections.admin.detailsPanel.submittedDate')}
					</dt>
					<dd class="mt-1 text-gray-900">{formatDate(selectedCorrection.created_at)}</dd>
				</div>

				<div>
					<dt class="text-sm font-medium text-gray-500">
						{$t('corrections.admin.detailsPanel.slaDeadline')}
					</dt>
					<dd class="mt-1 text-gray-900">
						{selectedCorrection.sla_deadline
							? formatDate(selectedCorrection.sla_deadline)
							: '-'}
					</dd>
				</div>
			</dl>

			<div class="mt-6 flex justify-end">
				<button
					onclick={closeDetailsPanel}
					class="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
				>
					{$t('corrections.admin.detailsPanel.close')}
				</button>
			</div>
		</div>
	</div>
{/if}
