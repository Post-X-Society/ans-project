<script lang="ts">
	import { goto } from '$app/navigation';
	import { currentUser } from '$lib/stores/auth';
	import { transitionWorkflowState } from '$lib/api/workflow';
	import type { PageData } from './$types';
	import type { Submission } from '$lib/api/types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Modal state
	let showApproveModal = $state(false);
	let showRequestChangesModal = $state(false);
	let showRejectModal = $state(false);
	let showPublishModal = $state(false);
	let showSendBackModal = $state(false);
	let selectedSubmission = $state<Submission | null>(null);
	let modalComment = $state('');
	let modalReason = $state('');
	let isSubmitting = $state(false);
	let modalError = $state<string | null>(null);

	// Computed: Filter submissions by workflow state
	const adminReviewSubmissions = $derived(
		data.submissions.items.filter((s) => s.workflow_state === 'admin_review')
	);

	const finalApprovalSubmissions = $derived(
		data.submissions.items.filter((s) => s.workflow_state === 'final_approval')
	);

	// Computed: Calculate reviewer workload (count of non-completed submissions per reviewer)
	interface ReviewerWorkload {
		reviewer_id: string;
		reviewer_name: string;
		reviewer_email: string;
		count: number;
	}

	const reviewerWorkload: ReviewerWorkload[] = $derived.by(() => {
		const workloadMap = new Map<string, ReviewerWorkload>();

		// Count all processing submissions per reviewer
		data.submissions.items
			.filter((s) => s.status === 'processing')
			.forEach((submission) => {
				submission.reviewers?.forEach((reviewer) => {
					const existing = workloadMap.get(reviewer.id);
					if (existing) {
						existing.count++;
					} else {
						workloadMap.set(reviewer.id, {
							reviewer_id: reviewer.id,
							reviewer_name: reviewer.name || reviewer.email,
							reviewer_email: reviewer.email,
							count: 1
						});
					}
				});
			});

		// Convert to array and sort by count descending
		return Array.from(workloadMap.values()).sort((a, b) => b.count - a.count);
	});

	const isSuperAdmin = $derived($currentUser?.role === 'super_admin');

	// Helper to format relative time
	function formatRelativeTime(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

		if (diffDays === 0) return 'today';
		if (diffDays === 1) return '1 day ago';
		if (diffDays < 7) return `${diffDays} days ago`;
		return `${Math.floor(diffDays / 7)} weeks ago`;
	}

	// Modal handlers
	function openApproveModal(submission: Submission) {
		selectedSubmission = submission;
		modalComment = '';
		modalError = null;
		showApproveModal = true;
	}

	function openRequestChangesModal(submission: Submission) {
		selectedSubmission = submission;
		modalComment = '';
		modalError = null;
		showRequestChangesModal = true;
	}

	function openRejectModal(submission: Submission) {
		selectedSubmission = submission;
		modalReason = '';
		modalError = null;
		showRejectModal = true;
	}

	function openPublishModal(submission: Submission) {
		selectedSubmission = submission;
		modalError = null;
		showPublishModal = true;
	}

	function openSendBackModal(submission: Submission) {
		selectedSubmission = submission;
		modalComment = '';
		modalError = null;
		showSendBackModal = true;
	}

	function closeModals() {
		showApproveModal = false;
		showRequestChangesModal = false;
		showRejectModal = false;
		showPublishModal = false;
		showSendBackModal = false;
		selectedSubmission = null;
		modalComment = '';
		modalReason = '';
		modalError = null;
	}

	// Action handlers
	async function handleApprove() {
		if (!selectedSubmission) return;

		isSubmitting = true;
		modalError = null;

		try {
			await transitionWorkflowState(selectedSubmission.id, {
				to_state: 'peer_review',
				comment: modalComment || undefined,
				actor: 'admin'
			});
			closeModals();
			window.location.reload(); // Reload to fetch updated data
		} catch (error) {
			console.error('Failed to approve submission:', error);
			modalError = 'Failed to approve submission. Please try again.';
			isSubmitting = false;
		}
	}

	async function handleRequestChanges() {
		if (!selectedSubmission || !modalComment.trim()) {
			modalError = 'Please provide a comment explaining the requested changes.';
			return;
		}

		isSubmitting = true;
		modalError = null;

		try {
			await transitionWorkflowState(selectedSubmission.id, {
				to_state: 'needs_more_research',
				comment: modalComment,
				actor: 'admin'
			});
			closeModals();
			window.location.reload();
		} catch (error) {
			console.error('Failed to request changes:', error);
			modalError = 'Failed to request changes. Please try again.';
			isSubmitting = false;
		}
	}

	async function handleReject() {
		if (!selectedSubmission || !modalReason.trim()) {
			modalError = 'Please provide a reason for rejection.';
			return;
		}

		isSubmitting = true;
		modalError = null;

		try {
			await transitionWorkflowState(selectedSubmission.id, {
				to_state: 'rejected',
				comment: modalReason,
				actor: 'admin'
			});
			closeModals();
			window.location.reload();
		} catch (error) {
			console.error('Failed to reject submission:', error);
			modalError = 'Failed to reject submission. Please try again.';
			isSubmitting = false;
		}
	}

	async function handlePublish() {
		if (!selectedSubmission) return;

		isSubmitting = true;
		modalError = null;

		try {
			await transitionWorkflowState(selectedSubmission.id, {
				to_state: 'published',
				actor: 'super_admin'
			});
			closeModals();
			window.location.reload();
		} catch (error) {
			console.error('Failed to publish submission:', error);
			modalError = 'Failed to publish submission. Please try again.';
			isSubmitting = false;
		}
	}

	async function handleSendBack() {
		if (!selectedSubmission) return;

		isSubmitting = true;
		modalError = null;

		try {
			await transitionWorkflowState(selectedSubmission.id, {
				to_state: 'peer_review',
				comment: modalComment || undefined,
				actor: 'super_admin'
			});
			closeModals();
			window.location.reload();
		} catch (error) {
			console.error('Failed to send back submission:', error);
			modalError = 'Failed to send back submission. Please try again.';
			isSubmitting = false;
		}
	}
</script>

<div class="container mx-auto px-4 py-8 max-w-7xl">
	<h1 class="text-3xl font-bold text-gray-900 mb-8">Admin Dashboard</h1>

	<!-- Pending Admin Review Section -->
	<section class="mb-10">
		<h2 class="text-2xl font-semibold text-gray-800 mb-4">
			Pending Admin Review ({adminReviewSubmissions.length})
		</h2>

		{#if adminReviewSubmissions.length === 0}
			<div
				class="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-600"
			>
				<svg
					class="w-16 h-16 mx-auto mb-4 text-gray-400"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
					></path>
				</svg>
				<p class="text-lg">No submissions pending admin review</p>
				<p class="text-sm text-gray-500 mt-2">All clear! No action required at this time.</p>
			</div>
		{:else}
			<div class="bg-white border border-gray-200 rounded-lg divide-y divide-gray-200">
				{#each adminReviewSubmissions as submission (submission.id)}
					<div class="p-4">
						<div class="flex items-start justify-between mb-3">
							<div class="flex-1 min-w-0">
								<h3 class="font-medium text-gray-900 mb-1">
									<a
										href="/submissions/{submission.id}"
										class="hover:text-primary-600 transition"
									>
										{submission.content.substring(0, 100)}{submission.content.length > 100
											? '...'
											: ''}
									</a>
								</h3>
								<div class="flex items-center gap-4 text-sm text-gray-600">
									<span>
										Reviewer: {submission.reviewers?.[0]?.name ||
											submission.reviewers?.[0]?.email ||
											'Unassigned'}
									</span>
									<span>Submitted: {formatRelativeTime(submission.updated_at)}</span>
								</div>
							</div>
						</div>
						<div class="flex gap-2">
							<button
								type="button"
								onclick={() => openApproveModal(submission)}
								class="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition"
							>
								Approve
							</button>
							<button
								type="button"
								onclick={() => openRequestChangesModal(submission)}
								class="px-4 py-2 bg-yellow-600 text-white text-sm font-medium rounded-lg hover:bg-yellow-700 transition"
							>
								Request Changes
							</button>
							<button
								type="button"
								onclick={() => openRejectModal(submission)}
								class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition"
							>
								Reject
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</section>

	<!-- Pending Final Approval Section (Super Admin Only) -->
	{#if isSuperAdmin}
		<section class="mb-10">
			<h2 class="text-2xl font-semibold text-gray-800 mb-4">
				Pending Final Approval ({finalApprovalSubmissions.length})
			</h2>

			{#if finalApprovalSubmissions.length === 0}
				<div
					class="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-600"
				>
					<svg
						class="w-16 h-16 mx-auto mb-4 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
						></path>
					</svg>
					<p class="text-lg">No submissions pending final approval</p>
					<p class="text-sm text-gray-500 mt-2">
						Submissions will appear here after passing peer review.
					</p>
				</div>
			{:else}
				<div class="bg-white border border-gray-200 rounded-lg divide-y divide-gray-200">
					{#each finalApprovalSubmissions as submission (submission.id)}
						<div class="p-4">
							<div class="flex items-start justify-between mb-3">
								<div class="flex-1 min-w-0">
									<h3 class="font-medium text-gray-900 mb-1">
										<a
											href="/submissions/{submission.id}"
											class="hover:text-primary-600 transition"
										>
											{submission.content.substring(0, 100)}{submission.content.length >
											100
												? '...'
												: ''}
										</a>
									</h3>
									<div class="text-sm text-gray-600">
										<span>Peer Review: Completed</span>
									</div>
								</div>
							</div>
							<div class="flex gap-2">
								<button
									type="button"
									onclick={() => openPublishModal(submission)}
									class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition"
								>
									Publish
								</button>
								<button
									type="button"
									onclick={() => openSendBackModal(submission)}
									class="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition"
								>
									Send Back
								</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>
	{/if}

	<!-- Reviewer Workload Section -->
	<section class="mb-10">
		<h2 class="text-2xl font-semibold text-gray-800 mb-4">Reviewer Workload</h2>

		{#if reviewerWorkload.length === 0}
			<div
				class="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-600"
			>
				<svg
					class="w-16 h-16 mx-auto mb-4 text-gray-400"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
					></path>
				</svg>
				<p class="text-lg">No reviewer workload data</p>
				<p class="text-sm text-gray-500 mt-2">No reviewers currently have assignments.</p>
			</div>
		{:else}
			<div class="bg-white border border-gray-200 rounded-lg p-6">
				<div class="space-y-4">
					{#each reviewerWorkload as workload (workload.reviewer_id)}
						{@const maxCount = Math.max(...reviewerWorkload.map((w) => w.count))}
						{@const widthPercent = Math.round((workload.count / maxCount) * 100)}
						<div>
							<div class="flex items-center justify-between mb-1">
								<span class="font-medium text-gray-900">{workload.reviewer_name}</span>
								<span class="text-sm text-gray-600">{workload.count} pending</span>
							</div>
							<div class="w-full bg-gray-200 rounded-full h-2">
								<div
									class="bg-primary-600 h-2 rounded-full transition-all"
									style="width: {widthPercent}%"
								></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</section>
</div>

<!-- Approve Modal -->
{#if showApproveModal && selectedSubmission}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		onclick={closeModals}
	>
		<div
			class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-xl font-semibold text-gray-900 mb-4">Approve Submission</h3>
			<p class="text-gray-700 mb-4">
				Approve this submission to move it to peer review? You can optionally add a comment.
			</p>

			<label for="approve-comment" class="block text-sm font-medium text-gray-700 mb-2">
				Comment (optional)
			</label>
			<textarea
				id="approve-comment"
				bind:value={modalComment}
				rows="3"
				class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
				placeholder="Add a comment..."
			></textarea>

			{#if modalError}
				<p class="mt-2 text-sm text-red-600">{modalError}</p>
			{/if}

			<div class="flex gap-2 mt-6">
				<button
					type="button"
					onclick={handleApprove}
					disabled={isSubmitting}
					class="flex-1 px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
				>
					{isSubmitting ? 'Approving...' : 'Approve'}
				</button>
				<button
					type="button"
					onclick={closeModals}
					disabled={isSubmitting}
					class="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition"
				>
					Cancel
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Request Changes Modal -->
{#if showRequestChangesModal && selectedSubmission}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		onclick={closeModals}
	>
		<div
			class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-xl font-semibold text-gray-900 mb-4">Request Changes</h3>
			<p class="text-gray-700 mb-4">
				Please explain what changes are needed for this submission.
			</p>

			<label for="changes-comment" class="block text-sm font-medium text-gray-700 mb-2">
				Comment *
			</label>
			<textarea
				id="changes-comment"
				bind:value={modalComment}
				rows="4"
				class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
				placeholder="Explain the requested changes..."
				required
			></textarea>

			{#if modalError}
				<p class="mt-2 text-sm text-red-600">{modalError}</p>
			{/if}

			<div class="flex gap-2 mt-6">
				<button
					type="button"
					onclick={handleRequestChanges}
					disabled={isSubmitting}
					class="flex-1 px-4 py-2 bg-yellow-600 text-white font-medium rounded-lg hover:bg-yellow-700 disabled:opacity-50 transition"
				>
					{isSubmitting ? 'Sending...' : 'Request Changes'}
				</button>
				<button
					type="button"
					onclick={closeModals}
					disabled={isSubmitting}
					class="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition"
				>
					Cancel
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Reject Modal -->
{#if showRejectModal && selectedSubmission}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		onclick={closeModals}
	>
		<div
			class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-xl font-semibold text-gray-900 mb-4">Reject Submission</h3>
			<p class="text-gray-700 mb-4">
				Please provide a reason for rejecting this submission.
			</p>

			<label for="reject-reason" class="block text-sm font-medium text-gray-700 mb-2">
				Reason *
			</label>
			<textarea
				id="reject-reason"
				bind:value={modalReason}
				rows="4"
				class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
				placeholder="Explain why this submission is being rejected..."
				required
			></textarea>

			{#if modalError}
				<p class="mt-2 text-sm text-red-600">{modalError}</p>
			{/if}

			<div class="flex gap-2 mt-6">
				<button
					type="button"
					onclick={handleReject}
					disabled={isSubmitting}
					class="flex-1 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition"
				>
					{isSubmitting ? 'Rejecting...' : 'Reject'}
				</button>
				<button
					type="button"
					onclick={closeModals}
					disabled={isSubmitting}
					class="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition"
				>
					Cancel
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Publish Modal -->
{#if showPublishModal && selectedSubmission}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		onclick={closeModals}
	>
		<div
			class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-xl font-semibold text-gray-900 mb-4">Publish Submission</h3>
			<p class="text-gray-700 mb-4">
				Publish this fact-check to make it publicly visible?
			</p>

			{#if modalError}
				<p class="mt-2 text-sm text-red-600">{modalError}</p>
			{/if}

			<div class="flex gap-2 mt-6">
				<button
					type="button"
					onclick={handlePublish}
					disabled={isSubmitting}
					class="flex-1 px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 transition"
				>
					{isSubmitting ? 'Publishing...' : 'Publish'}
				</button>
				<button
					type="button"
					onclick={closeModals}
					disabled={isSubmitting}
					class="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition"
				>
					Cancel
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Send Back Modal -->
{#if showSendBackModal && selectedSubmission}
	<div
		class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
		onclick={closeModals}
	>
		<div
			class="bg-white rounded-lg p-6 max-w-md w-full mx-4"
			onclick={(e) => e.stopPropagation()}
		>
			<h3 class="text-xl font-semibold text-gray-900 mb-4">Send Back to Peer Review</h3>
			<p class="text-gray-700 mb-4">
				Send this submission back to peer review? You can optionally add a comment.
			</p>

			<label for="sendback-comment" class="block text-sm font-medium text-gray-700 mb-2">
				Comment (optional)
			</label>
			<textarea
				id="sendback-comment"
				bind:value={modalComment}
				rows="3"
				class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
				placeholder="Add a comment..."
			></textarea>

			{#if modalError}
				<p class="mt-2 text-sm text-red-600">{modalError}</p>
			{/if}

			<div class="flex gap-2 mt-6">
				<button
					type="button"
					onclick={handleSendBack}
					disabled={isSubmitting}
					class="flex-1 px-4 py-2 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 transition"
				>
					{isSubmitting ? 'Sending...' : 'Send Back'}
				</button>
				<button
					type="button"
					onclick={closeModals}
					disabled={isSubmitting}
					class="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-lg hover:bg-gray-300 transition"
				>
					Cancel
				</button>
			</div>
		</div>
	</div>
{/if}
