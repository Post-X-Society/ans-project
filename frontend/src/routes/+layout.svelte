<script lang="ts">
	import '../app.css';
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import Header from '$lib/components/Header.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import CookieConsentBanner from '$lib/components/gdpr/CookieConsentBanner.svelte';
	import { initI18n } from '$lib/i18n';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	// Initialize i18n
	initI18n();

	// Create QueryClient instance for TanStack Query
	const queryClient = new QueryClient({
		defaultOptions: {
			queries: {
				staleTime: 1000 * 60 * 5, // 5 minutes
				refetchOnWindowFocus: false
			}
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<div class="flex flex-col min-h-screen">
		<Header />
		<Nav />
		<main class="flex-1">
			{@render children?.()}
		</main>
		<Footer />
	</div>
	<CookieConsentBanner />
</QueryClientProvider>
