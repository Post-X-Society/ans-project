<script lang="ts">
	import { createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { createSubmissionMutationOptions } from '$lib/api/queries';
	import type { SubmissionCreate } from '$lib/api/types';
	import { authStore } from '$lib/stores/auth';

	// Svelte 5 runes for reactive state
	let content = $state('');
	let submissionType = $state<'text' | 'image' | 'url'>('text');
	let errors = $state<{ content?: string }>({});

	const queryClient = useQueryClient();
	const mutation = createMutation(createSubmissionMutationOptions());

	// Check authentication
	let auth = $derived($authStore);
	let isAuthenticated = $derived(auth.isAuthenticated);

	// Computed values using $derived
	let characterCount = $derived(content.length);
	let isValid = $derived(content.length >= 10 && content.length <= 5000);

	// Validation function
	function validateForm(): boolean {
		errors = {};

		if (!content || content.trim().length === 0) {
			errors.content = 'Content is required and cannot be empty';
			return false;
		}

		if (content.length < 10) {
			errors.content = 'Content must be at least 10 characters';
			return false;
		}

		if (content.length > 5000) {
			errors.content = 'Content must be maximum 5000 characters';
			return false;
		}

		return true;
	}

	// Form submission handler
	async function handleSubmit(e: Event) {
		e.preventDefault();

		if (!validateForm()) {
			return;
		}

		const data: SubmissionCreate = {
			content: content.trim(),
			type: submissionType
		};

		$mutation.mutate(data, {
			onSuccess: () => {
				// Reset form on success
				content = '';
				submissionType = 'text';
				errors = {};
				// Invalidate submissions query to refetch
				queryClient.invalidateQueries({ queryKey: ['submissions'] });
			}
		});
	}
</script>

<form onsubmit={handleSubmit} class="space-y-6">
	<!-- Content Textarea -->
	<div>
		<label for="content" class="block text-sm font-medium text-gray-700 mb-2">
			Claim Content
		</label>
		<textarea
			id="content"
			bind:value={content}
			rows="6"
			class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
			class:border-red-500={errors.content}
			placeholder="Enter the claim or statement you want fact-checked..."
		></textarea>

		<!-- Character count -->
		<div class="flex justify-between items-center mt-1">
			<div>
				{#if errors.content}
					<p class="text-sm text-red-600">{errors.content}</p>
				{/if}
			</div>
			<p class="text-sm text-gray-500">{characterCount} / 5000</p>
		</div>
	</div>

	<!-- Submission Type Select -->
	<div>
		<label for="type" class="block text-sm font-medium text-gray-700 mb-2">
			Submission Type
		</label>
		<select
			id="type"
			bind:value={submissionType}
			class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
		>
			<option value="text">Text</option>
			<option value="image">Image</option>
			<option value="url">URL</option>
		</select>
	</div>

	<!-- Submit Button -->
	<div>
		<button
			type="submit"
			disabled={$mutation.isPending || !isAuthenticated}
			class="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
		>
			{#if $mutation.isPending}
				Submitting...
			{:else if !isAuthenticated}
				Please login to submit
			{:else}
				Submit for Fact-Checking
			{/if}
		</button>
		{#if !isAuthenticated}
			<p class="mt-2 text-sm text-gray-600 text-center">
				You must be logged in to submit claims.
				<a href="/login" class="text-primary-600 hover:text-primary-700 font-medium">
					Login here
				</a>
			</p>
		{/if}
	</div>

	<!-- Success Message -->
	{#if $mutation.isSuccess}
		<div class="bg-green-50 border border-green-200 rounded-lg p-4">
			<p class="text-green-800 font-medium">✓ Submission successful!</p>
			<p class="text-green-700 text-sm mt-1">
				Your claim has been submitted and will be fact-checked shortly.
			</p>
		</div>
	{/if}

	<!-- Error Message -->
	{#if $mutation.isError}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4">
			<p class="text-red-800 font-medium">✗ Submission failed</p>
			<p class="text-red-700 text-sm mt-1">
				{#if $mutation.error?.response?.status === 401}
					You are not authenticated. Please
					<a href="/login" class="underline font-medium">login</a> to submit claims.
				{:else}
					{$mutation.error?.message || 'An error occurred. Please try again.'}
				{/if}
			</p>
		</div>
	{/if}
</form>
