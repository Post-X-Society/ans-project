<script lang="ts">
	import type { Submission } from '$lib/api/types';
	import { currentUser } from '$lib/stores/auth';
	import { selfAssignToSubmission } from '$lib/api/submissions';
	import StatusBadge from './StatusBadge.svelte';
	import ReviewerAvatar from './ReviewerAvatar.svelte';
	import { t } from 'svelte-i18n';

	interface Props {
		submission: Submission;
	}

	let { submission }: Props = $props();

	// Self-assignment state
	let isAssigning = $state(false);
	let assignError = $state<string | null>(null);

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
	 * Get assignment badge text and classes
	 */
	function getAssignmentBadge(): { text: string; classes: string } {
		if (submission.is_assigned_to_me) {
			return {
				text: $t('submissions.assignment.assignedToYou'),
				classes: 'bg-green-100 text-green-800 border border-green-300'
			};
		}
		if (!submission.reviewers || submission.reviewers.length === 0) {
			return {
				text: $t('submissions.assignment.unassigned'),
				classes: 'bg-gray-100 text-gray-700'
			};
		}
		const count = submission.reviewers.length;
		return {
			text:
				count === 1
					? $t('submissions.assignment.reviewerSingular')
					: $t('submissions.assignment.reviewers', { values: { count } }),
			classes: 'bg-blue-100 text-blue-800'
		};
	}

	/**
	 * Get workflow status badge text and classes (if applicable)
	 */
	function getWorkflowBadge(): { text: string; classes: string } | null {
		const state = submission.workflow_state;

		if (!state) return null;

		switch (state) {
			case 'in_research':
			case 'draft_ready':
				return {
					text: 'In Progress',
					classes: 'bg-amber-100 text-amber-800'
				};
			case 'peer_review':
				return {
					text: 'Peer Review',
					classes: 'bg-purple-100 text-purple-800'
				};
			case 'published':
				return {
					text: 'Published',
					classes: 'bg-green-100 text-green-800'
				};
			case 'rejected':
				return {
					text: 'Rejected',
					classes: 'bg-red-100 text-red-800'
				};
			default:
				return null;
		}
	}

	/**
	 * Check if current user can self-assign
	 */
	function canSelfAssign(): boolean {
		if (!$currentUser) return false;
		if (submission.is_assigned_to_me) return false;
		const allowedRoles = ['reviewer', 'admin', 'super_admin'];
		return allowedRoles.includes($currentUser.role);
	}

	/**
	 * Handle self-assignment
	 */
	async function handleSelfAssign(event: Event) {
		event.preventDefault();
		event.stopPropagation();

		if (!canSelfAssign()) return;

		isAssigning = true;
		assignError = null;

		try {
			await selfAssignToSubmission(submission.id);
			// Reload the page to reflect the assignment
			window.location.reload();
		} catch (error) {
			console.error('Failed to self-assign:', error);
			assignError = $t('submissions.assignment.assignError');
			isAssigning = false;
		}
	}

	const assignmentBadge = $derived(getAssignmentBadge());
	const workflowBadge = $derived(getWorkflowBadge());
</script>

<div
	class="block bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow relative"
>
	<!-- Assignment Badge (top-right corner) -->
	<div class="absolute top-4 right-4 z-10 flex flex-col items-end gap-1">
		<span
			data-testid="assignment-badge"
			class="inline-flex items-center px-2 py-1 rounded-md text-xs font-semibold {assignmentBadge.classes}"
		>
			{assignmentBadge.text}
		</span>
		{#if workflowBadge}
			<span
				data-testid="workflow-badge"
				class="inline-flex items-center px-2 py-1 rounded-md text-xs font-semibold {workflowBadge.classes}"
			>
				{workflowBadge.text}
			</span>
		{/if}
	</div>

	<a href="/submissions/{submission.id}" class="block">
		<!-- Spotlight Video Thumbnail (if applicable) -->
		{#if submission.submission_type === 'spotlight' && submission.spotlight_content}
			<div class="relative bg-gray-900 aspect-video">
				<img
					src={submission.spotlight_content.thumbnail_url}
					alt="Spotlight thumbnail"
					class="w-full h-full object-contain"
				/>
				<div
					class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded"
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

			<!-- Assigned Reviewers with Avatars -->
			{#if submission.reviewers && submission.reviewers.length > 0}
				<div class="mb-3">
					<div class="text-xs text-gray-500 mb-1">Assigned Reviewers:</div>
					<div class="flex items-center gap-2">
						<!-- Show first 3 reviewer avatars -->
						{#each submission.reviewers.slice(0, 3) as reviewer}
							<ReviewerAvatar name={reviewer.name} email={reviewer.email} size="md" />
						{/each}
						<!-- Show +N more indicator if more than 3 reviewers -->
						{#if submission.reviewers.length > 3}
							<span
								data-testid="more-reviewers"
								class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600"
								title={submission.reviewers
									.slice(3)
									.map((r) => r.name || r.email)
									.join(', ')}
							>
								+{submission.reviewers.length - 3}
							</span>
						{/if}
					</div>
				</div>
			{/if}

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
	</a>

	<!-- Self-Assignment Button (bottom of card, outside link) -->
	{#if canSelfAssign()}
		<div class="px-4 pb-4">
			<button
				type="button"
				onclick={handleSelfAssign}
				disabled={isAssigning}
				aria-label={$t('submissions.assignment.ariaAssignToMe')}
				class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium text-sm"
			>
				{isAssigning ? $t('submissions.assignment.assigning') : $t('submissions.assignment.assignToMe')}
			</button>

			{#if assignError}
				<p class="mt-2 text-sm text-red-600 text-center">
					{assignError}
				</p>
			{/if}
		</div>
	{/if}
</div>
