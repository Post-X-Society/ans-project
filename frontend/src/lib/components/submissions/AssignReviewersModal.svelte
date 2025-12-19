<script lang="ts">
	import type { Submission, User } from '$lib/api/types';
	import { assignReviewer, removeReviewer } from '$lib/api/submissions';
	import { getUsers } from '$lib/api/users';
	import { onMount } from 'svelte';

	interface Props {
		submission: Submission;
		isOpen: boolean;
		onClose: () => void;
		onUpdate: () => void;
	}

	let { submission, isOpen, onClose, onUpdate }: Props = $props();

	// State
	let allUsers = $state<User[]>([]);
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let actionInProgress = $state<string | null>(null);

	// Derived state
	let availableReviewers = $derived(
		allUsers.filter(
			(user) =>
				['reviewer', 'admin', 'super_admin'].includes(user.role) &&
				!submission.reviewers.some((r) => r.id === user.id)
		)
	);

	/**
	 * Load all users when modal opens
	 */
	async function loadUsers() {
		if (allUsers.length > 0) return; // Already loaded

		isLoading = true;
		error = null;

		try {
			allUsers = await getUsers();
		} catch (err: any) {
			console.error('Error loading users:', err);
			error = err.response?.data?.detail || 'Failed to load users';
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Assign a reviewer
	 */
	async function handleAssign(reviewerId: string) {
		actionInProgress = reviewerId;
		error = null;

		try {
			await assignReviewer(submission.id, reviewerId);
			onUpdate(); // Refresh parent data
		} catch (err: any) {
			console.error('Error assigning reviewer:', err);
			error = err.response?.data?.detail || 'Failed to assign reviewer';
		} finally {
			actionInProgress = null;
		}
	}

	/**
	 * Remove a reviewer
	 */
	async function handleRemove(reviewerId: string) {
		actionInProgress = reviewerId;
		error = null;

		try {
			await removeReviewer(submission.id, reviewerId);
			onUpdate(); // Refresh parent data
		} catch (err: any) {
			console.error('Error removing reviewer:', err);
			error = err.response?.data?.detail || 'Failed to remove reviewer';
		} finally {
			actionInProgress = null;
		}
	}

	/**
	 * Handle escape key
	 */
	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Escape' && isOpen) {
			onClose();
		}
	}

	/**
	 * Load users when modal opens
	 */
	$effect(() => {
		if (isOpen) {
			loadUsers();
		}
	});
</script>

<svelte:window onkeydown={handleKeyDown} />

{#if isOpen}
	<div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
		<!-- Backdrop -->
		<div
			class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
			onclick={onClose}
			role="button"
			tabindex="-1"
		></div>

		<!-- Modal -->
		<div class="flex min-h-full items-center justify-center p-4">
			<div
				class="relative transform overflow-hidden rounded-lg bg-white shadow-xl transition-all w-full max-w-2xl"
			>
				<!-- Header -->
				<div class="bg-white px-6 pt-5 pb-4">
					<div class="flex items-center justify-between">
						<h3 class="text-lg font-medium text-gray-900" id="modal-title">
							Assign Reviewers
						</h3>
						<button
							onclick={onClose}
							class="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
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
				</div>

				<!-- Body -->
				<div class="px-6 pb-4">
					<!-- Error Message -->
					{#if error}
						<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
							<p class="text-sm text-red-800">{error}</p>
						</div>
					{/if}

					<!-- Loading State -->
					{#if isLoading}
						<div class="flex justify-center py-8">
							<div class="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"></div>
						</div>

					<!-- Loaded State -->
					{:else}
						<!-- Currently Assigned Reviewers -->
						<div class="mb-6">
							<h4 class="text-sm font-medium text-gray-700 mb-3">
								Currently Assigned ({submission.reviewers.length})
							</h4>

							{#if submission.reviewers.length === 0}
								<p class="text-sm text-gray-500 italic">No reviewers assigned yet</p>
							{:else}
								<div class="space-y-2">
									{#each submission.reviewers as reviewer}
										<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
											<div>
												<p class="text-sm font-medium text-gray-900">{reviewer.email}</p>
											</div>
											<button
												onclick={() => handleRemove(reviewer.id)}
												disabled={actionInProgress === reviewer.id}
												class="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition disabled:opacity-50"
											>
												{actionInProgress === reviewer.id ? 'Removing...' : 'Remove'}
											</button>
										</div>
									{/each}
								</div>
							{/if}
						</div>

						<!-- Available Reviewers -->
						<div>
							<h4 class="text-sm font-medium text-gray-700 mb-3">
								Available Reviewers ({availableReviewers.length})
							</h4>

							{#if availableReviewers.length === 0}
								<p class="text-sm text-gray-500 italic">No additional reviewers available</p>
							{:else}
								<div class="space-y-2 max-h-64 overflow-y-auto">
									{#each availableReviewers as user}
										<div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
											<div>
												<p class="text-sm font-medium text-gray-900">{user.email}</p>
												<p class="text-xs text-gray-500 capitalize">{user.role.replace('_', ' ')}</p>
											</div>
											<button
												onclick={() => handleAssign(user.id)}
												disabled={actionInProgress === user.id}
												class="px-3 py-1 text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded transition disabled:opacity-50"
											>
												{actionInProgress === user.id ? 'Assigning...' : 'Assign'}
											</button>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}
				</div>

				<!-- Footer -->
				<div class="bg-gray-50 px-6 py-4">
					<button
						onclick={onClose}
						class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
					>
						Close
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
