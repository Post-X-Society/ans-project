<!--
	CorrectionCard Component
	Issue #81: Frontend Public Corrections Log Page (TDD)

	Displays a single correction entry in the public corrections log.
	Shows correction type, date, summary of changes, and link to original fact-check.
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PublicLogCorrectionResponse, CorrectionType } from '$lib/api/types';

	interface Props {
		correction: PublicLogCorrectionResponse;
	}

	let { correction }: Props = $props();

	// Badge color classes based on correction type
	const typeBadgeColors: Record<CorrectionType, string> = {
		substantial: 'bg-orange-100 text-orange-800',
		update: 'bg-blue-100 text-blue-800',
		minor: 'bg-gray-100 text-gray-800'
	};

	// Status badge colors
	const statusBadgeColors: Record<string, string> = {
		accepted: 'bg-green-100 text-green-800',
		rejected: 'bg-red-100 text-red-800',
		pending: 'bg-yellow-100 text-yellow-800'
	};

	// Get the display date (reviewed_at or created_at as fallback)
	const displayDate = $derived(correction.reviewed_at || correction.created_at);

	// Format date for display
	const formattedDate = $derived(
		new Date(displayDate).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		})
	);

	// ISO date for datetime attribute
	const isoDate = $derived(new Date(displayDate).toISOString());

	// Truncate long text
	function truncateText(text: string, maxLength: number = 150): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength).trim() + '...';
	}

	// Truncated request details
	const truncatedDetails = $derived(truncateText(correction.request_details, 150));

	// Get localized correction type label
	const typeLabel = $derived($t(`correctionsLog.types.${correction.correction_type}`));

	// Get localized status label
	const statusLabel = $derived($t(`correctionsLog.status.${correction.status}`));
</script>

<article
	class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
	data-testid="correction-card"
	data-correction-id={correction.id}
>
	<div class="flex items-start justify-between gap-4">
		<div class="flex-1 min-w-0">
			<!-- Header with type badge and date -->
			<div class="flex items-center gap-2 mb-2 flex-wrap">
				<span
					class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {typeBadgeColors[
						correction.correction_type
					]}"
					data-testid="correction-type-badge"
				>
					{typeLabel}
				</span>
				<span
					class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {statusBadgeColors[
						correction.status
					] || 'bg-gray-100 text-gray-800'}"
					data-testid="correction-status-badge"
				>
					{statusLabel}
				</span>
				<time class="text-sm text-gray-500" datetime={isoDate}>
					{formattedDate}
				</time>
			</div>

			<!-- Correction title/heading -->
			<h3 class="text-lg font-medium text-gray-900 mb-2">
				{$t('correctionsLog.card.correctionApplied')}
			</h3>

			<!-- Request details summary -->
			<p class="text-sm text-gray-600 mb-3" data-testid="correction-details">
				{truncatedDetails}
			</p>

			<!-- Resolution notes if available -->
			{#if correction.resolution_notes}
				<div class="bg-gray-50 rounded-md p-3 mb-3">
					<p class="text-sm text-gray-700">
						<span class="font-medium">{$t('correctionsLog.card.changesApplied')}:</span>
						{correction.resolution_notes}
					</p>
				</div>
			{/if}

			<!-- Link to fact-check -->
			<a
				href="/submissions/{correction.fact_check_id}"
				class="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline"
				data-testid="fact-check-link"
			>
				{$t('correctionsLog.card.viewFactCheck')}
				<svg
					class="ml-1 w-4 h-4"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
					/>
				</svg>
			</a>
		</div>
	</div>
</article>
