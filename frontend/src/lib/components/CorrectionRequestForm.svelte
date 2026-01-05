<!--
  CorrectionRequestForm Component
  Issue #79: Frontend Correction Request Form (TDD)
  EPIC #50: Corrections & Complaints System

  Public-facing form for submitting correction requests on fact-checks.
  No authentication required - follows EFCSN 7-day SLA guidelines.
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import { submitCorrectionRequest } from '$lib/api/corrections';
	import type { CorrectionType, CorrectionSubmitResponse } from '$lib/api/types';

	interface Props {
		factCheckId: string;
		onSuccess?: () => void;
	}

	let { factCheckId, onSuccess }: Props = $props();

	// Form state using Svelte 5 runes
	let correctionType = $state<CorrectionType | ''>('');
	let requestDetails = $state('');
	let requesterEmail = $state('');

	// UI state
	let isSubmitting = $state(false);
	let submitSuccess = $state(false);
	let submitResponse = $state<CorrectionSubmitResponse | null>(null);

	// Error state
	let errors = $state<{
		correctionType?: string;
		requestDetails?: string;
		requesterEmail?: string;
		submit?: string;
	}>({});

	// Email validation regex
	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

	// Validation function
	function validateForm(): boolean {
		const newErrors: typeof errors = {};

		if (!correctionType) {
			newErrors.correctionType = $t('corrections.validation.typeRequired');
		}

		if (!requestDetails.trim()) {
			newErrors.requestDetails = $t('corrections.validation.detailsRequired');
		} else if (requestDetails.trim().length < 10) {
			newErrors.requestDetails = $t('corrections.validation.detailsMinLength');
		}

		if (requesterEmail && !emailRegex.test(requesterEmail)) {
			newErrors.requesterEmail = $t('corrections.validation.emailInvalid');
		}

		errors = newErrors;
		return Object.keys(newErrors).length === 0;
	}

	// Submit handler
	async function handleSubmit(event: Event) {
		event.preventDefault();

		if (!validateForm()) {
			return;
		}

		isSubmitting = true;
		errors = {};

		try {
			const response = await submitCorrectionRequest({
				fact_check_id: factCheckId,
				correction_type: correctionType as CorrectionType,
				request_details: requestDetails.trim(),
				requester_email: requesterEmail || undefined
			});

			submitResponse = response;
			submitSuccess = true;

			if (onSuccess) {
				onSuccess();
			}
		} catch (error) {
			errors.submit = $t('corrections.error.submitFailed');
		} finally {
			isSubmitting = false;
		}
	}

	// Format SLA deadline for display
	function formatDeadline(isoDate: string): string {
		try {
			const date = new Date(isoDate);
			return date.toLocaleDateString(undefined, {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		} catch {
			return isoDate;
		}
	}
</script>

<div class="correction-request-form">
	{#if submitSuccess && submitResponse}
		<!-- Success State -->
		<div class="success-message bg-green-50 border border-green-200 rounded-lg p-6">
			<h2 class="text-xl font-semibold text-green-800 mb-2">
				{$t('corrections.success.title')}
			</h2>
			<p class="text-green-700 mb-4">
				{$t('corrections.success.message')}
			</p>
			{#if submitResponse.sla_deadline}
				<p class="text-green-600 text-sm">
					{$t('corrections.success.slaNote', {
						values: { deadline: formatDeadline(submitResponse.sla_deadline) }
					})}
				</p>
			{/if}
			{#if submitResponse.acknowledgment_sent}
				<p class="text-green-600 text-sm mt-2">
					{$t('corrections.success.acknowledgmentSent')}
				</p>
			{/if}
		</div>
	{:else}
		<!-- Form -->
		<div class="mb-6">
			<h2 class="text-2xl font-bold text-gray-900 mb-2">
				{$t('corrections.title')}
			</h2>
			<p class="text-gray-600">
				{$t('corrections.description')}
			</p>
		</div>

		<form onsubmit={handleSubmit} novalidate class="space-y-6">
			<!-- Error Type Selection -->
			<div>
				<label for="correction-type" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('corrections.form.errorTypeLabel')}
				</label>
				<select
					id="correction-type"
					bind:value={correctionType}
					required
					aria-describedby={errors.correctionType ? 'correction-type-error' : undefined}
					class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
						{errors.correctionType ? 'border-red-500' : 'border-gray-300'}"
				>
					<option value="">{$t('corrections.form.errorTypePlaceholder')}</option>
					<option value="minor">{$t('corrections.types.minor')}</option>
					<option value="update">{$t('corrections.types.update')}</option>
					<option value="substantial">{$t('corrections.types.substantial')}</option>
				</select>
				{#if errors.correctionType}
					<p id="correction-type-error" class="mt-1 text-sm text-red-600">
						{errors.correctionType}
					</p>
				{/if}
			</div>

			<!-- Error Type Descriptions -->
			<div class="bg-gray-50 rounded-lg p-4 text-sm space-y-2">
				<div class="flex items-start gap-2">
					<span class="font-medium text-gray-700">{$t('corrections.types.minor')}:</span>
					<span class="text-gray-600">{$t('corrections.types.minorDescription')}</span>
				</div>
				<div class="flex items-start gap-2">
					<span class="font-medium text-gray-700">{$t('corrections.types.update')}:</span>
					<span class="text-gray-600">{$t('corrections.types.updateDescription')}</span>
				</div>
				<div class="flex items-start gap-2">
					<span class="font-medium text-gray-700">{$t('corrections.types.substantial')}:</span>
					<span class="text-gray-600">{$t('corrections.types.substantialDescription')}</span>
				</div>
			</div>

			<!-- Evidence/Details Textarea -->
			<div>
				<label for="request-details" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('corrections.form.detailsLabel')}
				</label>
				<textarea
					id="request-details"
					bind:value={requestDetails}
					required
					rows="5"
					aria-describedby={errors.requestDetails ? 'request-details-error' : undefined}
					placeholder={$t('corrections.form.detailsPlaceholder')}
					class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
						{errors.requestDetails ? 'border-red-500' : 'border-gray-300'}"
				></textarea>
				{#if errors.requestDetails}
					<p id="request-details-error" class="mt-1 text-sm text-red-600">
						{errors.requestDetails}
					</p>
				{/if}
			</div>

			<!-- Email Input (Optional) -->
			<div>
				<label for="requester-email" class="block text-sm font-medium text-gray-700 mb-1">
					{$t('corrections.form.emailLabel')}
				</label>
				<input
					id="requester-email"
					type="email"
					bind:value={requesterEmail}
					aria-describedby={errors.requesterEmail ? 'requester-email-error' : 'email-help'}
					placeholder={$t('corrections.form.emailPlaceholder')}
					class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
						{errors.requesterEmail ? 'border-red-500' : 'border-gray-300'}"
				/>
				{#if errors.requesterEmail}
					<p id="requester-email-error" class="mt-1 text-sm text-red-600">
						{errors.requesterEmail}
					</p>
				{:else}
					<p id="email-help" class="mt-1 text-sm text-gray-500">
						{$t('corrections.form.emailHelp')}
					</p>
				{/if}
			</div>

			<!-- Submit Error -->
			{#if errors.submit}
				<div class="bg-red-50 border border-red-200 rounded-lg p-4">
					<p class="text-red-700">{errors.submit}</p>
				</div>
			{/if}

			<!-- Submit Button -->
			<button
				type="submit"
				disabled={isSubmitting}
				class="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg
					hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
					disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
			>
				{#if isSubmitting}
					<span class="flex items-center justify-center gap-2">
						<svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
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
						{$t('corrections.form.submitting')}
					</span>
				{:else}
					{$t('corrections.form.submit')}
				{/if}
			</button>
		</form>

		<!-- EFCSN Escalation Link -->
		<div class="mt-8 pt-6 border-t border-gray-200">
			<p class="text-sm text-gray-600 mb-2">
				<a
					href="https://efcsn.com/complaints"
					target="_blank"
					rel="noopener noreferrer"
					class="text-blue-600 hover:text-blue-800 underline"
				>
					{$t('corrections.efcsn.escalateLink')}
				</a>
			</p>
			<p class="text-xs text-gray-500">
				{$t('corrections.efcsn.escalateDescription')}
			</p>
		</div>
	{/if}
</div>
