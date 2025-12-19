<script lang="ts">
	import type { Submission } from '$lib/api/types';
	import { currentUser, isAdmin } from '$lib/stores/auth';
	import StatusBadge from './StatusBadge.svelte';
	import AssignReviewersModal from './AssignReviewersModal.svelte';

	interface Props {
		submission: Submission;
		onUpdate?: () => void;
	}

	let { submission, onUpdate }: Props = $props();

	// Modal state
	let isAssignModalOpen = $state(false);

	/**
	 * Format date to readable string
	 */
	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	/**
	 * Format duration from milliseconds
	 */
	function formatDuration(ms: number): string {
		const seconds = Math.floor(ms / 1000);
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		if (minutes > 0) {
			return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
		}
		return `${seconds}s`;
	}

	/**
	 * Format view count
	 */
	function formatViewCount(count: number): string {
		if (count >= 1000000) {
			return `${(count / 1000000).toFixed(1)}M`;
		}
		if (count >= 1000) {
			return `${(count / 1000).toFixed(1)}K`;
		}
		return count.toString();
	}

	/**
	 * Truncate long content for display
	 */
	function truncateContent(content: string, maxLength: number = 150): string {
		if (content.length <= maxLength) return content;
		return content.slice(0, maxLength) + '...';
	}

	/**
	 * Get type badge classes
	 */
	function getTypeBadgeClasses(type: string): string {
		const baseClasses = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium';

		switch (type) {
			case 'text':
				return `${baseClasses} bg-purple-100 text-purple-800`;
			case 'image':
				return `${baseClasses} bg-pink-100 text-pink-800`;
			case 'url':
				return `${baseClasses} bg-indigo-100 text-indigo-800`;
			case 'spotlight':
				return `${baseClasses} bg-orange-100 text-orange-800`;
			default:
				return `${baseClasses} bg-gray-100 text-gray-800`;
		}
	}

	/**
	 * Check if a reviewer is the current user
	 */
	function isCurrentUserReviewer(reviewerId: string): boolean {
		return $currentUser?.id === reviewerId;
	}

	/**
	 * Open assign reviewers modal
	 */
	function openAssignModal(e: Event) {
		e.stopPropagation(); // Prevent card click
		isAssignModalOpen = true;
	}

	/**
	 * Handle modal update - refresh parent data
	 */
	function handleModalUpdate() {
		if (onUpdate) {
			onUpdate();
		}
	}
</script>

<div
	class="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
	onclick={() => {
		/* TODO: Navigate to submission detail page */
		console.log('View submission:', submission.id);
	}}
	role="button"
	tabindex="0"
	onkeydown={(e) => {
		if (e.key === 'Enter' || e.key === ' ') {
			console.log('View submission:', submission.id);
		}
	}}
>
	<!-- Spotlight Video Thumbnail (if applicable) -->
	{#if submission.submission_type === 'spotlight' && submission.spotlight_content}
		<div class="relative bg-gray-900 aspect-video">
			<img
				src={submission.spotlight_content.thumbnail_url}
				alt="Spotlight thumbnail"
				class="w-full h-full object-contain"
			/>
			<div
				class="absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded"
			>
				Snapchat Spotlight
			</div>
			{#if submission.spotlight_content.duration_ms}
				<div
					class="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded"
				>
					{formatDuration(submission.spotlight_content.duration_ms)}
				</div>
			{/if}
		</div>
	{/if}

	<div class="p-4">
		<!-- Header: Type and Status -->
		<div class="flex items-center justify-between mb-3">
			<div class="flex items-center space-x-2">
				<span class={getTypeBadgeClasses(submission.submission_type)}>
					{submission.submission_type}
				</span>
			</div>
			<StatusBadge status={submission.status} />
		</div>

		<!-- Spotlight Creator Info -->
		{#if submission.submission_type === 'spotlight' && submission.spotlight_content}
			<div class="mb-3">
				<div class="flex items-center space-x-2">
					<svg
						class="w-5 h-5 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
						/>
					</svg>
					<span class="font-medium text-gray-900">
						{submission.spotlight_content.creator_name ||
							submission.spotlight_content.creator_username ||
							'Unknown Creator'}
					</span>
				</div>
				{#if submission.spotlight_content.view_count}
					<div class="flex items-center space-x-2 mt-1 text-sm text-gray-600">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
							/>
						</svg>
						<span>{formatViewCount(submission.spotlight_content.view_count)} views</span>
					</div>
				{/if}
			</div>
		{:else}
			<!-- Content Preview for non-Spotlight submissions -->
			<p class="text-gray-700 mb-3 line-clamp-2">
				{truncateContent(submission.content)}
			</p>
		{/if}

		<!-- Submitter Info -->
		{#if submission.user}
			<div class="flex items-center space-x-2 mb-3 text-sm text-gray-600">
				<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
					/>
				</svg>
				<span>Submitted by {submission.user.email}</span>
			</div>
		{/if}

		<!-- Assigned Reviewers -->
		<div class="mb-3">
			<div class="flex items-center justify-between mb-1">
				<div class="text-xs text-gray-500">Assigned Reviewers:</div>
				{#if $isAdmin}
					<button
						onclick={openAssignModal}
						class="text-xs text-primary-600 hover:text-primary-700 font-medium"
					>
						Manage
					</button>
				{/if}
			</div>

			{#if submission.reviewers && submission.reviewers.length > 0}
				<div class="flex flex-wrap gap-1">
					{#each submission.reviewers.slice(0, 3) as reviewer}
						<span
							class={isCurrentUserReviewer(reviewer.id)
								? 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-300'
								: 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700'}
						>
							{reviewer.email}
						</span>
					{/each}
					{#if submission.reviewers.length > 3}
						<span
							class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600"
						>
							+{submission.reviewers.length - 3} more
						</span>
					{/if}
				</div>
			{:else}
				<p class="text-xs text-gray-400 italic">No reviewers assigned</p>
			{/if}
		</div>

		<!-- Footer: Date -->
		<div class="flex items-center text-sm text-gray-500">
			<svg
				class="w-4 h-4 mr-1"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			{formatDate(submission.created_at)}
		</div>
	</div>
</div>

<!-- Assign Reviewers Modal -->
<AssignReviewersModal
	{submission}
	isOpen={isAssignModalOpen}
	onClose={() => (isAssignModalOpen = false)}
	onUpdate={handleModalUpdate}
/>
