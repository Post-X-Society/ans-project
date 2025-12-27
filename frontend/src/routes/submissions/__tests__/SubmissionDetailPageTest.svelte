<script lang="ts">
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import SubmissionDetailPage from '../[id]/+page.svelte';

	interface Props {
		id: string;
	}

	let { id }: Props = $props();

	const queryClient = new QueryClient({
		defaultOptions: {
			queries: { retry: false },
			mutations: { retry: false }
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<SubmissionDetailPage data={{ id }} />
</QueryClientProvider>
