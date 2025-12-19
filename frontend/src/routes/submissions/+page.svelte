<script lang="ts">
	import { authStore } from '$lib/stores/auth';
	import SubmissionsList from '$lib/components/submissions/SubmissionsList.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let auth = $derived($authStore);

	/**
	 * Get role-specific welcome message
	 */
	function getWelcomeMessage(role: string): string {
		switch (role) {
			case 'super_admin':
			case 'admin':
				return 'View and manage all submissions from all users.';
			case 'reviewer':
				return 'View all submissions for fact-checking and review.';
			case 'submitter':
				return 'View your submitted content and track their status.';
			default:
				return 'View your submissions here.';
		}
	}

	/**
	 * Get role badge styling
	 */
	function getRoleBadgeClasses(role: string): string {
		const baseClasses = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium';
		switch (role) {
			case 'super_admin':
				return `${baseClasses} bg-purple-100 text-purple-800`;
			case 'admin':
				return `${baseClasses} bg-blue-100 text-blue-800`;
			case 'reviewer':
				return `${baseClasses} bg-green-100 text-green-800`;
			case 'submitter':
				return `${baseClasses} bg-gray-100 text-gray-800`;
			default:
				return baseClasses;
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-7xl mx-auto">
		<!-- Page Header -->
		<div class="mb-8">
			<div class="flex items-center justify-between mb-4">
				<h1 class="text-3xl font-bold text-gray-900">Submissions</h1>
				{#if auth.user}
					<span class={getRoleBadgeClasses(auth.user.role)}>
						{auth.user.role.replace('_', ' ').toUpperCase()}
					</span>
				{/if}
			</div>

			<p class="text-gray-600">
				{auth.user ? getWelcomeMessage(auth.user.role) : 'View submissions here.'}
			</p>

			<!-- Quick Actions -->
			<div class="mt-4 flex flex-wrap gap-3">
				<a
					href="/submit"
					class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
				>
					<svg
						class="w-5 h-5 mr-2"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
					New Submission
				</a>

				{#if auth.user && (auth.user.role === 'admin' || auth.user.role === 'super_admin')}
					<a
						href="/admin"
						class="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium"
					>
						<svg
							class="w-5 h-5 mr-2"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
							/>
						</svg>
						Admin Panel
					</a>
				{/if}
			</div>
		</div>

		<!-- Submissions List Component -->
		<SubmissionsList initialData={data.submissions} />
	</div>
</div>
