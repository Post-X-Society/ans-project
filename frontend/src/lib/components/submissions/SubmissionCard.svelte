<script lang="ts">
	import type { Submission } from '$lib/api/types';
	import StatusBadge from './StatusBadge.svelte';

	interface Props {
		submission: Submission;
	}

	let { submission }: Props = $props();

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
	 * Truncate long content for display
	 */
	function truncateContent(content: string, maxLength: number = 150): string {
		if (content.length <= maxLength) return content;
		return content.slice(0, maxLength) + '...';
	}

	/**
	 * Truncate UUID for display (show first 8 characters)
	 */
	function truncateId(id: string): string {
		return id.slice(0, 8);
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
</script>

<div
	class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
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
	<!-- Header: ID, Type, and Status -->
	<div class="flex items-center justify-between mb-3">
		<div class="flex items-center space-x-2">
			<span class="text-sm font-mono text-gray-500">#{truncateId(submission.id)}</span>
			<span class={getTypeBadgeClasses(submission.submission_type)}>
				{submission.submission_type}
			</span>
		</div>
		<StatusBadge status={submission.status} />
	</div>

	<!-- Content Preview -->
	<p class="text-gray-700 mb-3 line-clamp-2">
		{truncateContent(submission.content)}
	</p>

	<!-- Footer: Date and User -->
	<div class="flex items-center justify-between text-sm text-gray-500">
		<span class="flex items-center">
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
		</span>
		{#if submission.user_id}
			<span class="text-xs font-mono text-gray-400">
				User: {truncateId(submission.user_id)}
			</span>
		{/if}
	</div>
</div>
