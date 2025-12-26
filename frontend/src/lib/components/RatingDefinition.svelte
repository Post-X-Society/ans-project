<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FactCheckRatingValue } from '$lib/api/types';

	type BadgeSize = 'sm' | 'md' | 'lg';
	type TooltipPosition = 'top' | 'bottom';

	interface Props {
		rating: FactCheckRatingValue;
		size?: BadgeSize;
		compact?: boolean;
		position?: TooltipPosition;
		class?: string;
	}

	let {
		rating,
		size = 'sm',
		compact = false,
		position = 'bottom',
		class: className = ''
	}: Props = $props();

	let isOpen = $state(false);
	let isPinned = $state(false);

	/**
	 * Rating configuration with colors matching EFCSN visual design
	 */
	const ratingConfig: Record<
		FactCheckRatingValue,
		{ bgClass: string; textClass: string; icon: string }
	> = {
		true: { bgClass: 'bg-emerald-100', textClass: 'text-emerald-800', icon: '✓' },
		partly_false: { bgClass: 'bg-orange-100', textClass: 'text-orange-800', icon: '⚠' },
		false: { bgClass: 'bg-red-100', textClass: 'text-red-800', icon: '✗' },
		missing_context: { bgClass: 'bg-yellow-100', textClass: 'text-yellow-800', icon: 'ℹ' },
		altered: { bgClass: 'bg-purple-100', textClass: 'text-purple-800', icon: '🖼' },
		satire: { bgClass: 'bg-blue-100', textClass: 'text-blue-800', icon: '😄' },
		unverifiable: { bgClass: 'bg-gray-100', textClass: 'text-gray-800', icon: '?' }
	};

	const sizeClasses: Record<BadgeSize, string> = {
		sm: 'px-2 py-0.5 text-xs',
		md: 'px-2.5 py-1 text-sm',
		lg: 'px-3 py-1.5 text-base'
	};

	const tooltipId = $derived(`rating-definition-${rating}-${Math.random().toString(36).slice(2)}`);

	const config = $derived(ratingConfig[rating] || ratingConfig.unverifiable);
	const ratingName = $derived($t(`ratings.${rating}.name`));
	const ratingDescription = $derived($t(`ratings.${rating}.description`));
	const ratingClasses = $derived(`${config.bgClass} ${config.textClass} ${sizeClasses[size]}`);

	const positionClasses = $derived(
		position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
	);

	function handleMouseEnter() {
		isOpen = true;
	}

	function handleMouseLeave() {
		if (!isPinned) {
			isOpen = false;
		}
	}

	function handleFocus() {
		isOpen = true;
	}

	function handleBlur() {
		if (!isPinned) {
			isOpen = false;
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			isPinned = !isPinned;
			isOpen = isPinned;
		} else if (event.key === 'Escape') {
			isPinned = false;
			isOpen = false;
		}
	}
</script>

<div class="relative inline-block {className}">
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
	<span
		role="status"
		tabindex="0"
		aria-describedby={isOpen ? tooltipId : undefined}
		aria-expanded={isOpen ? 'true' : 'false'}
		aria-label={$t('ratings.ariaLabel', { values: { rating: ratingName } })}
		class="inline-flex items-center gap-1 rounded-full font-medium cursor-help focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 {ratingClasses}"
		onmouseenter={handleMouseEnter}
		onmouseleave={handleMouseLeave}
		onfocus={handleFocus}
		onblur={handleBlur}
		onkeydown={handleKeyDown}
	>
		<span aria-hidden="true">{config.icon}</span>
		{#if !compact}
			<span>{ratingName}</span>
		{/if}
	</span>

	{#if isOpen}
		<div
			id={tooltipId}
			role="tooltip"
			class="absolute {positionClasses} left-0 z-50 w-64 p-3 bg-white rounded-lg shadow-lg border border-gray-200 text-sm"
		>
			<div class="font-semibold text-gray-900 mb-1">
				{ratingName}
			</div>
			<p class="text-gray-600">
				{ratingDescription}
			</p>
			<div
				class="absolute w-2 h-2 bg-white border-gray-200 transform rotate-45 {position === 'top'
					? 'bottom-[-5px] border-r border-b'
					: 'top-[-5px] border-l border-t'} left-4"
			></div>
		</div>
	{/if}
</div>
