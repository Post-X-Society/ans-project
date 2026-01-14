<script lang="ts">
	import { createSpotlightSubmission } from '$lib/api/submissions';
	import { authStore } from '$lib/stores/auth';
	import type { SpotlightContent } from '$lib/api/types';
	import { t } from '$lib/i18n';

	// Svelte 5 runes for reactive state
	let spotlightLink = $state('');
	let submitterComment = $state('');
	let errors = $state<{ link?: string; submit?: string }>({});
	let isSubmitting = $state(false);
	let submissionResult = $state<SpotlightContent | null>(null);

	const auth = $derived($authStore);
	const isAuthenticated = $derived(auth.isAuthenticated);

	// Character counter constants - Issue #177
	const MAX_COMMENT_LENGTH = 500;
	const WARNING_THRESHOLD = 450;

	// Derived state for character counter
	const commentLength = $derived(submitterComment.length);
	const isNearLimit = $derived(commentLength >= WARNING_THRESHOLD);
	const isAtLimit = $derived(commentLength >= MAX_COMMENT_LENGTH);

	// Validation function
	function validateForm(): boolean {
		errors = {};

		if (!spotlightLink || spotlightLink.trim().length === 0) {
			errors.link = $t('submissions.spotlightLinkRequired');
			return false;
		}

		// Basic URL validation
		try {
			const url = new URL(spotlightLink);
			if (!url.hostname.includes('snapchat.com') || !url.pathname.includes('spotlight')) {
				errors.link = $t('submissions.spotlightLinkInvalid');
				return false;
			}
		} catch {
			errors.link = $t('validation.invalidUrl');
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

		isSubmitting = true;
		errors = {};
		submissionResult = null;

		try {
			const result = await createSpotlightSubmission({
				spotlight_link: spotlightLink.trim(),
				submitter_comment: submitterComment.trim() || undefined
			});

			submissionResult = result;
			spotlightLink = ''; // Reset form
			submitterComment = ''; // Reset comment field
		} catch (error: any) {
			console.error('Submission error:', error);
			if (error.response?.data?.detail) {
				errors.submit = error.response.data.detail;
			} else {
				errors.submit = $t('submissions.submissionFailedMessage');
			}
		} finally {
			isSubmitting = false;
		}
	}
</script>

<form onsubmit={handleSubmit} class="space-y-6">
	<!-- Spotlight Link Input -->
	<div>
		<label for="spotlight-link" class="block text-sm font-medium text-gray-700 mb-2">
			{$t('submissions.spotlightLink')}
		</label>
		<input
			id="spotlight-link"
			type="url"
			bind:value={spotlightLink}
			class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition"
			class:border-red-500={errors.link}
			placeholder={$t('submissions.spotlightLinkPlaceholder')}
			disabled={isSubmitting || !isAuthenticated}
		/>

		{#if errors.link}
			<p class="text-sm text-red-600 mt-1">{errors.link}</p>
		{/if}

		<p class="text-sm text-gray-500 mt-2">
			{$t('submissions.spotlightLinkHelp')}
		</p>
	</div>

	<!-- Additional Context / Submitter Comment - Issue #177 -->
	<div>
		<label for="submitter-comment" class="block text-sm font-medium text-gray-700 mb-2">
			{$t('submissions.additionalContext')}
			<span class="text-gray-500 font-normal">({$t('common.optional')})</span>
		</label>
		<textarea
			id="submitter-comment"
			bind:value={submitterComment}
			class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition resize-none"
			placeholder={$t('submissions.additionalContextPlaceholder')}
			disabled={isSubmitting || !isAuthenticated}
			maxlength={MAX_COMMENT_LENGTH}
			rows="3"
		></textarea>
		<div class="flex justify-between items-center mt-1">
			<p class="text-sm text-gray-500">
				{$t('submissions.additionalContextHelp')}
			</p>
			<span
				class="text-sm transition-colors"
				class:text-gray-500={!isNearLimit}
				class:text-amber-600={isNearLimit && !isAtLimit}
				class:text-red-600={isAtLimit}
			>
				{commentLength}/{MAX_COMMENT_LENGTH}
			</span>
		</div>
	</div>

	<!-- Submit Button -->
	<div>
		<button
			type="submit"
			disabled={isSubmitting || !isAuthenticated}
			class="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
		>
			{#if isSubmitting}
				<span class="flex items-center justify-center">
					<svg
						class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle
							class="opacity-25"
							cx="12"
							cy="12"
							r="10"
							stroke="currentColor"
							stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					{$t('submissions.fetchingContent')}
				</span>
			{:else if !isAuthenticated}
				{$t('submissions.pleaseLoginToSubmit')}
			{:else}
				{$t('submissions.submitForFactCheck')}
			{/if}
		</button>

		{#if !isAuthenticated}
			<p class="mt-2 text-sm text-gray-600 text-center">
				{$t('submissions.mustBeLoggedIn')}
				<a href="/login" class="text-primary-600 hover:text-primary-700 font-medium">
					{$t('auth.loginHere')}
				</a>
			</p>
		{/if}
	</div>

	<!-- Success Message -->
	{#if submissionResult}
		<div class="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
			<p class="text-green-800 font-medium">{$t('submissions.submissionSuccess')}</p>

			<div class="space-y-2 text-sm">
				{#if submissionResult.creator_name}
					<p class="text-green-700">
						<span class="font-medium">{$t('submissions.creator')}</span>
						{submissionResult.creator_name}
						{#if submissionResult.creator_username}
							(@{submissionResult.creator_username})
						{/if}
					</p>
				{/if}

				{#if submissionResult.view_count}
					<p class="text-green-700">
						{$t('submissions.views', { values: { count: submissionResult.view_count.toLocaleString() } })}
					</p>
				{/if}

				{#if submissionResult.duration_ms}
					<p class="text-green-700">
						<span class="font-medium">{$t('submissions.duration')}</span>
						{Math.round(submissionResult.duration_ms / 1000)}s
					</p>
				{/if}
			</div>

			<p class="text-green-700 text-sm">
				{$t('submissions.videoDownloaded')}
			</p>
		</div>
	{/if}

	<!-- Error Message -->
	{#if errors.submit}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4">
			<p class="text-red-800 font-medium">{$t('submissions.submissionFailed')}</p>
			<p class="text-red-700 text-sm mt-1">{errors.submit}</p>
		</div>
	{/if}
</form>
