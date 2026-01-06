<!--
  Account Deletion Request Page

  Issue #92: Backend: Right to be Forgotten Workflow (TDD)
  EPIC #53: GDPR & Data Retention Compliance

  Allows users to submit GDPR Article 17 deletion requests
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import { createRTBFRequest, getUserDataSummary } from '$lib/api/rtbf';
	import type { UserDataSummary } from '$lib/api/types';
	import { onMount } from 'svelte';

	let reason = $state('');
	let dateOfBirth = $state('');
	let confirmed = $state(false);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);
	let dataSummary = $state<UserDataSummary | null>(null);
	let loadingSummary = $state(true);

	// Load data summary on mount
	onMount(async () => {
		try {
			dataSummary = await getUserDataSummary();
		} catch (err) {
			console.error('Failed to load data summary:', err);
		} finally {
			loadingSummary = false;
		}
	});

	async function handleSubmit() {
		error = null;

		// Validation
		if (!reason.trim()) {
			error = $t('rtbf.form.reasonRequired');
			return;
		}

		if (!confirmed) {
			error = $t('rtbf.form.confirmRequired');
			return;
		}

		isSubmitting = true;

		try {
			await createRTBFRequest({
				reason: reason.trim(),
				date_of_birth: dateOfBirth || undefined
			});

			// Show success and redirect
			alert($t('rtbf.form.success'));
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : $t('rtbf.form.error');
		} finally {
			isSubmitting = false;
		}
	}

	function cancel() {
		goto('/');
	}
</script>

<svelte:head>
	<title>{$t('rtbf.form.title')} | {$t('common.appName')}</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-3xl mx-auto">
		<!-- Warning Banner -->
		<div class="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
			<div class="flex">
				<div class="flex-shrink-0">
					<svg
						class="h-5 w-5 text-red-400"
						viewBox="0 0 20 20"
						fill="currentColor"
					>
						<path
							fill-rule="evenodd"
							d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<div class="ml-3">
					<h3 class="text-sm font-medium text-red-800">
						{$t('rtbf.form.title')}
					</h3>
					<div class="mt-2 text-sm text-red-700">
						<p>{$t('rtbf.form.description')}</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Data Summary -->
		{#if !loadingSummary && dataSummary}
			<div class="bg-white shadow rounded-lg p-6 mb-6">
				<h2 class="text-lg font-semibold text-gray-900 mb-4">Your Data Summary</h2>
				<dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<div class="bg-gray-50 px-4 py-3 rounded">
						<dt class="text-sm font-medium text-gray-500">Submissions</dt>
						<dd class="mt-1 text-2xl font-semibold text-gray-900">
							{dataSummary.submissions_count}
						</dd>
					</div>
					<div class="bg-gray-50 px-4 py-3 rounded">
						<dt class="text-sm font-medium text-gray-500">Published Submissions</dt>
						<dd class="mt-1 text-2xl font-semibold text-gray-900">
							{dataSummary.published_submissions_count}
						</dd>
					</div>
					<div class="bg-gray-50 px-4 py-3 rounded">
						<dt class="text-sm font-medium text-gray-500">Corrections</dt>
						<dd class="mt-1 text-2xl font-semibold text-gray-900">
							{dataSummary.corrections_count}
						</dd>
					</div>
					<div class="bg-gray-50 px-4 py-3 rounded">
						<dt class="text-sm font-medium text-gray-500">Ratings</dt>
						<dd class="mt-1 text-2xl font-semibold text-gray-900">
							{dataSummary.ratings_count}
						</dd>
					</div>
				</dl>
				{#if dataSummary.published_submissions_count > 0}
					<p class="mt-4 text-sm text-gray-600">
						Note: Your {dataSummary.published_submissions_count} published submission(s) will be
						anonymized (author removed) to preserve the integrity of the fact-checks.
					</p>
				{/if}
			</div>
		{/if}

		<!-- Form -->
		<div class="bg-white shadow rounded-lg">
			<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="p-6 space-y-6">
				<!-- Reason -->
				<div>
					<label for="reason" class="block text-sm font-medium text-gray-700">
						{$t('rtbf.form.reasonLabel')}
						<span class="text-red-600">*</span>
					</label>
					<textarea
						id="reason"
						bind:value={reason}
						rows="4"
						class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
						placeholder={$t('rtbf.form.reasonPlaceholder')}
						required
					></textarea>
				</div>

				<!-- Date of Birth -->
				<div>
					<label for="dob" class="block text-sm font-medium text-gray-700">
						{$t('rtbf.form.dateOfBirthLabel')}
					</label>
					<input
						id="dob"
						type="date"
						bind:value={dateOfBirth}
						class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
					/>
					<p class="mt-1 text-sm text-gray-500">
						{$t('rtbf.form.dateOfBirthHelp')}
					</p>
				</div>

				<!-- Confirmation -->
				<div class="flex items-start">
					<div class="flex items-center h-5">
						<input
							id="confirm"
							type="checkbox"
							bind:checked={confirmed}
							class="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
						/>
					</div>
					<div class="ml-3 text-sm">
						<label for="confirm" class="font-medium text-gray-700">
							{$t('rtbf.form.confirmLabel')}
							<span class="text-red-600">*</span>
						</label>
					</div>
				</div>

				<!-- Error Message -->
				{#if error}
					<div class="bg-red-50 border border-red-200 rounded-md p-4">
						<p class="text-sm text-red-800">{error}</p>
					</div>
				{/if}

				<!-- Actions -->
				<div class="flex justify-end space-x-4">
					<button
						type="button"
						onclick={cancel}
						class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
					>
						{$t('rtbf.form.cancel')}
					</button>
					<button
						type="submit"
						disabled={isSubmitting || !confirmed || !reason.trim()}
						class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{#if isSubmitting}
							<span class="flex items-center">
								<svg
									class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
								{$t('common.loading')}
							</span>
						{:else}
							{$t('rtbf.form.submit')}
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</div>
