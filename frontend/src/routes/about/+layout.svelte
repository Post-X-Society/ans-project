<!--
  About Section Layout

  Issue #85: Frontend: Public Transparency Pages
  EPIC #51: Transparency & Methodology Pages

  Provides a two-column layout with navigation sidebar for transparency pages.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { t } from '$lib/i18n';
	import TransparencyNav from '$lib/components/transparency/TransparencyNav.svelte';
	import LanguageSelector from '$lib/components/LanguageSelector.svelte';

	// Get the current slug from the URL
	let currentSlug = $derived($page.params.slug || '');
</script>

<div class="bg-gray-50 py-8">
	<div class="container mx-auto px-4">
		<!-- Breadcrumb -->
		<nav class="mb-6" aria-label="Breadcrumb">
			<ol class="flex items-center space-x-2 text-sm text-gray-500">
				<li>
					<a href="/" class="hover:text-gray-700">{$t('nav.home')}</a>
				</li>
				<li>
					<span class="mx-2">/</span>
				</li>
				<li>
					<span class="text-gray-900 font-medium">{$t('transparency.title')}</span>
				</li>
			</ol>
		</nav>

		<!-- Two-column layout -->
		<div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
			<!-- Sidebar with navigation -->
			<aside class="lg:col-span-1">
				<div class="sticky top-4 space-y-4">
					<TransparencyNav {currentSlug} />

					<!-- Language selector -->
					<div class="bg-white rounded-lg shadow-sm p-4">
						<div class="flex items-center justify-between">
							<span class="text-sm text-gray-600">{$t('language.select')}</span>
							<LanguageSelector />
						</div>
					</div>
				</div>
			</aside>

			<!-- Main content area -->
			<div class="lg:col-span-3">
				<slot />
			</div>
		</div>
	</div>
</div>
