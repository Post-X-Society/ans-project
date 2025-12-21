<script lang="ts">
	import '../app.css';
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import Header from '$lib/components/Header.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import { initI18n } from '$lib/i18n';

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
			<slot />
		</main>
		<Footer />
	</div>
</QueryClientProvider>
