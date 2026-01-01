<!--
  PeerReviewDashboard Component

  Issue #67: Frontend: Peer Review Dashboard (TDD)
  EPIC #48: Multi-Tier Approval & Peer Review
  ADR 0005: EFCSN Compliance Architecture

  Features:
  - List pending peer reviews for current user
  - Display fact-check details and supporting evidence
  - Approve/reject form with reviewer comments
  - Visual consensus indicators
  - Notification badge for pending reviews
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { t, getCurrentLocale } from '$lib/i18n';
	import { getPendingReviews, getPeerReviewStatus, submitPeerReview } from '$lib/api/peer-review';
	import type {
		PendingReviewsResponse,
		PeerReviewStatusResponse,
		PendingReviewItem,
		ApprovalStatus
	} from '$lib/api/types';

	// State
	let pendingReviews = $state<PendingReviewsResponse | null>(null);
	let selectedReviewStatus = $state<PeerReviewStatusResponse | null>(null);
	let selectedReviewId = $state<string | null>(null);
	let isLoading = $state(true);
	let isLoadingDetails = $state(false);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let submitError = $state<string | null>(null);
	let submitSuccess = $state(false);
	let comments = $state('');

	// Derived state
	let pendingCount = $derived(pendingReviews?.total_count ?? 0);
	let selectedFactCheckId = $derived(
		pendingReviews?.reviews.find((r) => r.id === selectedReviewId)?.fact_check_id ?? null
	);

	onMount(() => {
		loadPendingReviews();
	});

	async function loadPendingReviews() {
		isLoading = true;
		error = null;
		try {
			pendingReviews = await getPendingReviews();
		} catch (err: unknown) {
			console.error('Error loading pending reviews:', err);
			error = $t('peerReview.error');
		} finally {
			isLoading = false;
		}
	}

	async function selectReview(review: PendingReviewItem) {
		selectedReviewId = review.id;
		isLoadingDetails = true;
		submitSuccess = false;
		submitError = null;
		comments = '';

		try {
			selectedReviewStatus = await getPeerReviewStatus(review.fact_check_id, 1);
		} catch (err: unknown) {
			console.error('Error loading review status:', err);
		} finally {
			isLoadingDetails = false;
		}
	}

	async function handleSubmitReview(approved: boolean) {
		if (!selectedFactCheckId) return;

		isSubmitting = true;
		submitError = null;
		submitSuccess = false;

		try {
			await submitPeerReview(selectedFactCheckId, {
				approved,
				comments: comments.trim() || null
			});
			submitSuccess = true;

			// Refresh the pending reviews list
			await loadPendingReviews();

			// Clear selection if the review was submitted
			selectedReviewId = null;
			selectedReviewStatus = null;
			comments = '';
		} catch (err: unknown) {
			console.error('Error submitting review:', err);
			submitError = $t('peerReview.reviewFailed');
		} finally {
			isSubmitting = false;
		}
	}

	function formatDate(dateString: string): string {
		const locale = getCurrentLocale();
		return new Date(dateString).toLocaleDateString(locale === 'nl' ? 'nl-NL' : 'en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusBadgeClass(status: ApprovalStatus): string {
		const baseClass = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
		switch (status) {
			case 'approved':
				return `${baseClass} bg-green-100 text-green-800`;
			case 'rejected':
				return `${baseClass} bg-red-100 text-red-800`;
			case 'pending':
				return `${baseClass} bg-yellow-100 text-yellow-800`;
			default:
				return baseClass;
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-6xl mx-auto">
		<!-- Header with notification badge -->
		<div class="flex justify-between items-center mb-6">
			<div class="flex items-center gap-3">
				<h1 class="text-3xl font-bold text-gray-900">{$t('peerReview.title')}</h1>
				{#if pendingCount > 0}
					<span
						class="inline-flex items-center justify-center px-2.5 py-1 text-sm font-bold leading-none text-white bg-red-600 rounded-full"
					>
						{pendingCount}
					</span>
				{/if}
			</div>
		</div>

		{#if isLoading}
			<div class="text-center py-12">
				<p class="text-gray-600">{$t('peerReview.loading')}</p>
			</div>
		{:else if error}
			<div class="bg-red-50 border border-red-200 rounded-lg p-4">
				<p class="text-red-800">{error}</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- Pending Reviews List -->
				<div class="lg:col-span-1">
					<div class="bg-white shadow rounded-lg overflow-hidden">
						<div class="px-4 py-3 border-b border-gray-200">
							<h2 class="text-lg font-semibold text-gray-900">
								{$t('peerReview.pendingReviews')}
							</h2>
						</div>

						{#if pendingReviews && pendingReviews.reviews.length > 0}
							<ul class="divide-y divide-gray-200">
								{#each pendingReviews.reviews as review (review.id)}
									<li>
										<button
											data-testid="pending-review-item"
											onclick={() => selectReview(review)}
											class="w-full px-4 py-3 text-left hover:bg-gray-50 transition {selectedReviewId ===
											review.id
												? 'bg-primary-50 border-l-4 border-primary-600'
												: ''}"
										>
											<div class="flex justify-between items-start">
												<div>
													<p class="text-sm font-medium text-gray-900">
														{$t('peerReview.factCheckId')}: {review.fact_check_id.slice(0, 8)}...
													</p>
													<p class="text-xs text-gray-500 mt-1">
														{formatDate(review.created_at)}
													</p>
												</div>
												<span class={getStatusBadgeClass('pending')}>
													{$t('peerReview.pending')}
												</span>
											</div>
										</button>
									</li>
								{/each}
							</ul>
						{:else}
							<div class="px-4 py-8 text-center">
								<p class="text-gray-500">{$t('peerReview.noPendingReviews')}</p>
								<p class="text-sm text-gray-400 mt-1">
									{$t('peerReview.noPendingReviewsMessage')}
								</p>
							</div>
						{/if}
					</div>
				</div>

				<!-- Review Details Panel -->
				<div class="lg:col-span-2">
					{#if selectedReviewId && selectedReviewStatus}
						<div data-testid="review-detail-panel" class="bg-white shadow rounded-lg overflow-hidden">
							<div class="px-6 py-4 border-b border-gray-200">
								<h2 class="text-lg font-semibold text-gray-900">
									{$t('peerReview.reviewDetails')}
								</h2>
							</div>

							<div class="p-6 space-y-6">
								<!-- Success/Error Messages -->
								{#if submitSuccess}
									<div class="bg-green-50 border border-green-200 rounded-lg p-4">
										<p class="text-green-800">{$t('peerReview.reviewSubmitted')}</p>
									</div>
								{/if}

								{#if submitError}
									<div class="bg-red-50 border border-red-200 rounded-lg p-4">
										<p class="text-red-800">{submitError}</p>
									</div>
								{/if}

								<!-- Consensus Status -->
								<div>
									<h3 class="text-sm font-medium text-gray-700 mb-3">
										{$t('peerReview.consensusStatus')}
									</h3>

									<div
										data-testid="consensus-progress-bar"
										class="relative h-4 bg-gray-200 rounded-full overflow-hidden"
									>
										{#if selectedReviewStatus.total_reviews > 0}
											<div
												class="absolute left-0 top-0 h-full bg-green-500"
												style="width: {(selectedReviewStatus.approved_count /
													selectedReviewStatus.total_reviews) *
													100}%"
											></div>
											<div
												class="absolute top-0 h-full bg-red-500"
												style="left: {(selectedReviewStatus.approved_count /
													selectedReviewStatus.total_reviews) *
													100}%; width: {(selectedReviewStatus.rejected_count /
													selectedReviewStatus.total_reviews) *
													100}%"
											></div>
										{/if}
									</div>

									<div class="flex justify-between mt-3 text-sm">
										<span class="text-green-600">
											{selectedReviewStatus.approved_count} Approved
										</span>
										<span class="text-red-600">
											{selectedReviewStatus.rejected_count} Rejected
										</span>
										<span class="text-yellow-600">
											{selectedReviewStatus.pending_count} Pending
										</span>
									</div>

									{#if selectedReviewStatus.consensus_reached}
										<div
											class="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800"
										>
											{$t('peerReview.consensusReached')}
										</div>
									{:else}
										<div
											class="mt-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800"
										>
											{$t('peerReview.consensusNotReached')}
										</div>
									{/if}
								</div>

								<!-- Other Reviewers' Decisions -->
								<div>
									<h3 class="text-sm font-medium text-gray-700 mb-3">
										{$t('peerReview.otherReviewers')}
									</h3>

									{#if selectedReviewStatus.reviews.length > 0}
										<ul class="space-y-2">
											{#each selectedReviewStatus.reviews as review (review.id)}
												{#if review.approval_status !== 'pending'}
													<li class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
														<span class={getStatusBadgeClass(review.approval_status)}>
															{review.approval_status === 'approved'
																? $t('peerReview.approved')
																: $t('peerReview.rejected')}
														</span>
														{#if review.comments}
															<p class="text-sm text-gray-600 flex-1">{review.comments}</p>
														{/if}
													</li>
												{/if}
											{/each}
										</ul>
									{:else}
										<p class="text-sm text-gray-500">{$t('peerReview.noOtherReviews')}</p>
									{/if}
								</div>

								<!-- Your Decision Form -->
								<div class="border-t border-gray-200 pt-6">
									<h3 class="text-sm font-medium text-gray-700 mb-3">
										{$t('peerReview.yourDecision')}
									</h3>

									<div class="space-y-4">
										<div>
											<label for="comments" class="block text-sm font-medium text-gray-700 mb-1">
												{$t('peerReview.comments')}
											</label>
											<textarea
												id="comments"
												bind:value={comments}
												rows="3"
												class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
												placeholder={$t('peerReview.commentsPlaceholder')}
											></textarea>
										</div>

										<div class="flex gap-3">
											<button
												onclick={() => handleSubmitReview(true)}
												disabled={isSubmitting}
												class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition font-medium"
											>
												{isSubmitting ? $t('peerReview.submitting') : $t('peerReview.approve')}
											</button>
											<button
												onclick={() => handleSubmitReview(false)}
												disabled={isSubmitting}
												class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 transition font-medium"
											>
												{isSubmitting ? $t('peerReview.submitting') : $t('peerReview.reject')}
											</button>
										</div>
									</div>
								</div>
							</div>
						</div>
					{:else if isLoadingDetails}
						<div class="bg-white shadow rounded-lg p-8 text-center">
							<p class="text-gray-600">{$t('common.loading')}</p>
						</div>
					{:else}
						<div class="bg-white shadow rounded-lg p-8 text-center">
							<p class="text-gray-500">{$t('peerReview.selectReview')}</p>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>
