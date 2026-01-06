<!--
  TransparencyPage Component

  Issue #85: Frontend: Public Transparency Pages
  EPIC #51: Transparency & Methodology Pages

  Fetches and displays a single transparency page with markdown content.
  Supports multilingual content (EN/NL) and shows last updated timestamp.
-->
<script lang="ts">
	import { locale, t } from '$lib/i18n';
	import { getTransparencyPage } from '$lib/api/transparency';
	import { exportUserData } from '$lib/api/rtbf';
	import type { TransparencyPage as TransparencyPageType } from '$lib/api/types';
	import type { SupportedLocale } from '$lib/i18n';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	interface Props {
		slug: string;
	}

	let { slug }: Props = $props();

	let page = $state<TransparencyPageType | null>(null);
	let error = $state<string | null>(null);
	let isLoading = $state(true);

	// Current locale for content selection
	let currentLocale = $derived(($locale as SupportedLocale) || 'en');

	// Get title in current language, fallback to English
	let title = $derived(
		page ? (page.title[currentLocale] || page.title['en'] || 'Untitled') : ''
	);

	// Get content in current language, fallback to English
	let content = $derived(
		page ? (page.content[currentLocale] || page.content['en'] || '') : ''
	);

	// Parse markdown to HTML and sanitize for XSS protection
	// Content is admin-controlled from the transparency pages API but we still sanitize
	let renderedContent = $derived(() => {
		if (!content) return '';
		const html = marked.parse(content);
		// Only sanitize in browser environment
		if (browser && typeof html === 'string') {
			return DOMPurify.sanitize(html);
		}
		return typeof html === 'string' ? html : '';
	});

	// Format the last updated date
	let formattedDate = $derived(() => {
		if (!page?.updated_at) return '';
		const date = new Date(page.updated_at);
		return new Intl.DateTimeFormat(currentLocale === 'nl' ? 'nl-NL' : 'en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		}).format(date);
	});

	// Fetch the page data
	async function loadPage() {
		isLoading = true;
		error = null;

		try {
			page = await getTransparencyPage(slug, currentLocale);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load page';
			page = null;
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadPage();
	});

	// Reload when slug changes
	$effect(() => {
		if (slug) {
			loadPage();
		}
	});

	// Handle data export
	async function handleExport() {
		try {
			const data = await exportUserData();
			// Create download link
			const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `my-data-export-${new Date().toISOString().split('T')[0]}.json`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (err) {
			alert('Failed to export data. Please make sure you are logged in.');
		}
	}
</script>

{#if isLoading}
	<div class="flex items-center justify-center py-12">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
		<span class="ml-3 text-gray-600">{$t('transparency.loadingPage')}</span>
	</div>
{:else if error}
	<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
		<h2 class="text-lg font-semibold text-red-800 mb-2">{$t('common.error')}</h2>
		<p class="text-red-600">{error}</p>
		<button
			onclick={() => loadPage()}
			class="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
		>
			{$t('common.tryAgain')}
		</button>
	</div>
{:else if page}
	<article class="bg-white rounded-lg shadow-sm">
		<!-- Header -->
		<header class="border-b border-gray-200 px-6 py-4">
			<h1 class="text-2xl font-bold text-gray-900">{title}</h1>
			<div class="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
				<span>
					{$t('transparency.lastUpdated', { values: { date: formattedDate() } })}
				</span>
				<span class="hidden sm:inline">•</span>
				<span>
					{$t('transparency.version', { values: { version: page.version } })}
				</span>
			</div>
		</header>

		<!-- Content: HTML is sanitized with DOMPurify to prevent XSS -->
		<div class="px-6 py-6">
			<div class="prose prose-gray max-w-none">
				<!-- eslint-disable-next-line svelte/no-at-html-tags -- sanitized with DOMPurify -->
				{@html renderedContent()}
			</div>

			<!-- RTBF Section for Privacy Policy -->
			{#if slug === 'privacy-policy'}
				<div class="mt-8 pt-8 border-t border-gray-200">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">
						{$t('rtbf.privacySection.title')}
					</h2>
					<p class="text-gray-600 mb-4">
						{$t('rtbf.privacySection.description')}
					</p>
					<div class="flex flex-col sm:flex-row gap-4">
						<a
							href="/account/delete"
							class="inline-flex items-center justify-center px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium"
						>
							{$t('rtbf.requestDeletion')}
						</a>
						<button
							onclick={handleExport}
							class="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
						>
							{$t('rtbf.exportData')}
						</button>
					</div>
					<p class="text-sm text-gray-500 mt-4">
						{$t('rtbf.privacySection.note')}
					</p>
				</div>
			{/if}
		</div>
	</article>
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
