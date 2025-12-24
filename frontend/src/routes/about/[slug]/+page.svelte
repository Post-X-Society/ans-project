<!--
  Transparency Page Route

  Issue #85: Frontend: Public Transparency Pages
  EPIC #51: Transparency & Methodology Pages

  Dynamic route for displaying individual transparency pages.
  Valid slugs: methodology, organization, team, funding, partnerships,
               corrections-policy, privacy-policy
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { t } from '$lib/i18n';
	import { isValidTransparencySlug } from '$lib/api/transparency';
	import TransparencyPage from '$lib/components/transparency/TransparencyPage.svelte';

	// Get slug from route params
	let slug = $derived($page.params.slug);

	// Validate slug and redirect if invalid
	$effect(() => {
		if (slug && !isValidTransparencySlug(slug)) {
			// Redirect to methodology page if slug is invalid
			goto('/about/methodology');
		}
	});
</script>

<svelte:head>
	<title>{$t(`transparency.pages.${slug}`)} | {$t('common.appName')}</title>
	<meta name="description" content={$t(`transparency.descriptions.${slug}`)} />
</svelte:head>

{#if slug && isValidTransparencySlug(slug)}
	<TransparencyPage {slug} />
{:else}
	<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
		<h2 class="text-lg font-semibold text-yellow-800 mb-2">{$t('transparency.pageNotFound')}</h2>
		<p class="text-yellow-600">{$t('transparency.pageNotFoundMessage')}</p>
		<a
			href="/about/methodology"
			class="mt-4 inline-block px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
		>
			{$t('transparency.backToAbout')}
		</a>
	</div>
{/if}
