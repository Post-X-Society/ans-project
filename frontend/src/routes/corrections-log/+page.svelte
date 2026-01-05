<!--
	Corrections Log Page
	Issue #81: Frontend Public Corrections Log Page (TDD)
	EPIC #50: Corrections & Complaints System

	Public page displaying substantial corrections made over the last 24 months.
	Per EFCSN compliance requirements.
-->
<script lang="ts">
	import { t } from 'svelte-i18n';
	import CorrectionsList from '$lib/components/corrections/CorrectionsList.svelte';
</script>

<svelte:head>
	<title>{$t('correctionsLog.meta.title')} | Ans Fact-Checking</title>
	<meta name="description" content={$t('correctionsLog.meta.description')} />
	<link rel="alternate" type="application/rss+xml" title={$t('correctionsLog.rss.title')} href="/corrections-log/rss.xml" />
</svelte:head>

<main class="min-h-screen bg-gray-50">
	<div class="container mx-auto px-4 py-8">
		<div class="max-w-4xl mx-auto">
			<!-- Breadcrumb / Navigation -->
			<nav class="mb-6" aria-label="Breadcrumb">
				<ol class="flex items-center space-x-2 text-sm text-gray-600">
					<li>
						<a href="/" class="hover:text-blue-600 transition-colors">
							{$t('common.home')}
						</a>
					</li>
					<li>
						<span class="mx-2">/</span>
					</li>
					<li class="text-gray-900 font-medium" aria-current="page">
						{$t('correctionsLog.title')}
					</li>
				</ol>
			</nav>

			<!-- Page Header -->
			<header class="mb-8">
				<div class="flex items-start justify-between flex-wrap gap-4">
					<div>
						<h1 class="text-3xl font-bold text-gray-900 mb-3">
							{$t('correctionsLog.title')}
						</h1>
						<p class="text-gray-600 max-w-2xl">
							{$t('correctionsLog.description')}
						</p>
					</div>

					<!-- RSS Feed Link -->
					<a
						href="/corrections-log/rss.xml"
						class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
						title={$t('correctionsLog.rss.subscribe')}
					>
						<svg
							class="w-5 h-5 mr-2 text-orange-500"
							fill="currentColor"
							viewBox="0 0 24 24"
							data-testid="rss-icon"
						>
							<path
								d="M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19 7.38 20 6.18 20C5 20 4 19 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1z"
							/>
						</svg>
						{$t('correctionsLog.rss.feedLink')}
					</a>
				</div>

				<!-- EFCSN Compliance Notice -->
				<div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
					<div class="flex items-start">
						<svg
							class="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<div>
							<h2 class="text-sm font-medium text-blue-800">
								{$t('correctionsLog.efcsn.title')}
							</h2>
							<p class="mt-1 text-sm text-blue-700">
								{$t('correctionsLog.efcsn.notice')}
							</p>
						</div>
					</div>
				</div>
			</header>

			<!-- Corrections List -->
			<CorrectionsList pageSize={10} />

			<!-- Footer with additional transparency info -->
			<footer class="mt-12 pt-8 border-t border-gray-200">
				<div class="text-sm text-gray-600">
					<h2 class="font-medium text-gray-900 mb-2">
						{$t('correctionsLog.footer.aboutTitle')}
					</h2>
					<p class="mb-4">
						{$t('correctionsLog.footer.aboutText')}
					</p>
					<div class="flex flex-wrap gap-4">
						<a
							href="/about/methodology"
							class="text-blue-600 hover:text-blue-800 hover:underline"
						>
							{$t('correctionsLog.footer.methodologyLink')}
						</a>
						<a
							href="/about/corrections-policy"
							class="text-blue-600 hover:text-blue-800 hover:underline"
						>
							{$t('correctionsLog.footer.policyLink')}
						</a>
						<a
							href="https://efcsn.com/code-of-principles/"
							target="_blank"
							rel="noopener noreferrer"
							class="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center"
						>
							{$t('correctionsLog.footer.efcsnLink')}
							<svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
			</footer>
		</div>
	</div>
</main>
