<!--
  TransparencyNav Component

  Issue #85: Frontend: Public Transparency Pages
  EPIC #51: Transparency & Methodology Pages

  Displays navigation menu for all transparency pages.
  Uses svelte-i18n for multilingual support.
-->
<script lang="ts">
	import { t } from '$lib/i18n';
	import { TRANSPARENCY_PAGE_SLUGS } from '$lib/api/transparency';
	import type { TransparencyPageSlug } from '$lib/api/types';

	interface Props {
		currentSlug?: TransparencyPageSlug | string;
	}

	let { currentSlug }: Props = $props();
</script>

<nav aria-label={$t('transparency.navTitle')} class="bg-white rounded-lg shadow-sm p-4">
	<h2 class="text-lg font-semibold text-gray-900 mb-4">{$t('transparency.title')}</h2>

	<ul class="space-y-1">
		{#each TRANSPARENCY_PAGE_SLUGS as slug}
			{@const isActive = currentSlug === slug}
			<li>
				<a
					href="/about/{slug}"
					aria-current={isActive ? 'page' : undefined}
					class="block px-3 py-2 rounded-md text-sm transition-colors duration-150
						{isActive
						? 'bg-primary-100 text-primary-700 font-medium'
						: 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}"
				>
					{$t(`transparency.pages.${slug}`)}
				</a>
			</li>
		{/each}
	</ul>
</nav>
