<!--
  Admin Transparency Page Editor Route

  Issue #86: Frontend: Admin Transparency Page Editor
  EPIC #51: Transparency & Methodology Pages

  This route wraps the TransparencyEditor component and handles
  admin-only access control and slug parameter extraction.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { isAdmin, isAuthenticated } from '$lib/stores/auth';
	import { t } from '$lib/i18n';
	import TransparencyEditor from '$lib/components/transparency/TransparencyEditor.svelte';

	// Get slug from URL params
	let slug = $derived($page.params.slug);
	let canAccess = $derived($isAuthenticated && $isAdmin);
	let isCheckingAuth = $state(true);

	onMount(() => {
		// Wait a tick for auth state to load from localStorage
		setTimeout(() => {
			isCheckingAuth = false;

			// Use get() to access store value inside callback
			const currentPage = get(page);
			const authenticated = get(isAuthenticated);
			const admin = get(isAdmin);

			if (!authenticated) {
				goto('/login?redirect=' + encodeURIComponent(currentPage.url.pathname));
			} else if (!admin) {
				goto('/');
			}
		}, 100);
	});
</script>

<svelte:head>
	<title>{$t('transparency.editor.title')} | {$t('common.appName')}</title>
</svelte:head>

{#if isCheckingAuth}
	<div class="flex items-center justify-center min-h-screen">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
	</div>
{:else if !canAccess}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-gray-900 mb-4">{$t('errors.unauthorized')}</h1>
			<p class="text-gray-600 mb-4">
				You must be an admin to access this page.
			</p>
			<a href="/login" class="text-primary-600 hover:text-primary-800">
				{$t('nav.login')}
			</a>
		</div>
	</div>
{:else}
	<TransparencyEditor {slug} />
{/if}
