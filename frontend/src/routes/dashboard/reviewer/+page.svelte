<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	import SubmissionCard from '$lib/components/submissions/SubmissionCard.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Helper to format relative time for completed submissions
	function formatRelativeTime(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

		if (diffDays === 0) return 'today';
		if (diffDays === 1) return '1 day ago';
		if (diffDays < 7) return `${diffDays} days ago`;
		if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
		return `${Math.floor(diffDays / 30)} months ago`;
	}

	// Helper to calculate days until deadline
	function daysUntilDeadline(dueDateString: string): number {
		const dueDate = new Date(dueDateString);
		const now = new Date();
		const diffMs = dueDate.getTime() - now.getTime();
		return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
	}
</script>

<div class="container mx-auto px-4 py-8 max-w-7xl">
	<h1 class="text-3xl font-bold text-gray-900 mb-8">Reviewer Dashboard</h1>

	<!-- My Active Assignments Section -->
	<section class="mb-10">
		<h2 class="text-2xl font-semibold text-gray-800 mb-4">
			My Active Assignments ({data.activeAssignments.total})
		</h2>

		{#if data.activeAssignments.items.length === 0}
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
						d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
					></path>
				</svg>
				<p class="text-lg">No active assignments</p>
				<p class="text-sm text-gray-500 mt-2">
					Visit the <a href="/submissions" class="text-primary-600 hover:underline"
						>submissions page</a
					> to assign yourself to a submission.
				</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each data.activeAssignments.items as submission (submission.id)}
					<SubmissionCard {submission} />
				{/each}
			</div>
		{/if}
	</section>

	<!-- Pending Peer Reviews Section -->
	<section class="mb-10">
		<h2 class="text-2xl font-semibold text-gray-800 mb-4">
			Pending Peer Reviews ({data.pendingReviews.total})
		</h2>

		{#if data.pendingReviews.pending_reviews.length === 0}
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
				<p class="text-lg">No pending peer reviews</p>
				<p class="text-sm text-gray-500 mt-2">
					You don't have any fact-checks awaiting your peer review.
				</p>
			</div>
		{:else}
			<div class="space-y-3">
				{#each data.pendingReviews.pending_reviews as review (review.id)}
					{@const daysLeft = daysUntilDeadline(review.due_date)}
					<div
						class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
					>
						<div class="flex items-start justify-between">
							<div class="flex-1">
								<h3 class="font-medium text-gray-900 mb-1">
									{review.fact_check_title}
								</h3>
								<p class="text-sm text-gray-600">
									Requested by <span class="font-medium"
										>{review.requester.name || review.requester.email}</span
									>
									<span
										class="ml-2 text-xs px-2 py-0.5 rounded-full {daysLeft <= 2
											? 'bg-red-100 text-red-800'
											: daysLeft <= 5
												? 'bg-yellow-100 text-yellow-800'
												: 'bg-blue-100 text-blue-800'}"
									>
										Due in {daysLeft}
										{daysLeft === 1 ? 'day' : 'days'}
									</span>
								</p>
							</div>
							<button
								type="button"
								onclick={() => goto(`/admin/peer-review?fact_check_id=${review.fact_check_id}`)}
								class="ml-4 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition"
							>
								Review Now
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</section>

	<!-- Recently Completed Section -->
	<section class="mb-10">
		<h2 class="text-2xl font-semibold text-gray-800 mb-4">
			Recently Completed ({data.completedSubmissions.total})
		</h2>

		{#if data.completedSubmissions.items.length === 0}
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
						d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
					></path>
				</svg>
				<p class="text-lg">No completed submissions yet</p>
				<p class="text-sm text-gray-500 mt-2">
					Completed submissions will appear here.
				</p>
			</div>
		{:else}
			<div class="bg-white border border-gray-200 rounded-lg divide-y divide-gray-200">
				{#each data.completedSubmissions.items as submission (submission.id)}
					<a
						href="/submissions/{submission.id}"
						class="block p-4 hover:bg-gray-50 transition-colors"
					>
						<div class="flex items-center justify-between">
							<div class="flex-1 min-w-0">
								<p class="font-medium text-gray-900 truncate">
									{submission.content.substring(0, 80)}{submission.content.length > 80
										? '...'
										: ''}
								</p>
								<p class="text-sm text-gray-500 mt-1">
									Completed {formatRelativeTime(submission.updated_at)}
								</p>
							</div>
							<svg
								class="w-5 h-5 text-green-500 ml-4 flex-shrink-0"
								fill="currentColor"
								viewBox="0 0 20 20"
							>
								<path
									fill-rule="evenodd"
									d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
									clip-rule="evenodd"
								></path>
							</svg>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</section>
</div>
