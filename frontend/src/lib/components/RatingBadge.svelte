<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FactCheckRatingValue } from '$lib/api/types';

	type BadgeSize = 'sm' | 'md' | 'lg';

	interface Props {
		rating: FactCheckRatingValue;
		size?: BadgeSize;
		compact?: boolean;
		interactive?: boolean;
	}

	let { rating, size = 'sm', compact = false, interactive = false }: Props = $props();

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

	/**
	 * Size classes for different badge sizes
	 */
	const sizeClasses: Record<BadgeSize, string> = {
		sm: 'px-2 py-0.5 text-xs',
		md: 'px-2.5 py-1 text-sm',
		lg: 'px-3 py-1.5 text-base'
	};

	const config = $derived(ratingConfig[rating] || ratingConfig.unverifiable);
	const ratingName = $derived($t(`ratings.${rating}.name`));
	const ariaLabel = $derived($t('ratings.ariaLabel', { values: { rating: ratingName } }));

	const badgeClasses = $derived(
		[
			'inline-flex items-center gap-1 rounded-full font-medium',
			config.bgClass,
			config.textClass,
			sizeClasses[size],
			interactive ? 'cursor-pointer hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-1' : ''
		].join(' ')
	);
</script>

<span
	role="status"
	aria-label={ariaLabel}
	class={badgeClasses}
	tabindex={interactive ? 0 : undefined}
>
	<span aria-hidden="true">{config.icon}</span>
	{#if !compact}
		<span>{ratingName}</span>
	{/if}
</span>
