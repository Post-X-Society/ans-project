<script lang="ts">
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import CorrectionsList from '../CorrectionsList.svelte';

	interface Props {
		pageSize?: number;
	}

	let { pageSize = 10 }: Props = $props();

	const queryClient = new QueryClient({
		defaultOptions: {
			queries: { retry: false },
			mutations: { retry: false }
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<CorrectionsList {pageSize} />
</QueryClientProvider>
