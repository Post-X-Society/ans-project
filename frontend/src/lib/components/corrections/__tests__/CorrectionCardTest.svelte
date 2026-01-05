<script lang="ts">
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import CorrectionCard from '../CorrectionCard.svelte';
	import type { PublicLogCorrectionResponse } from '$lib/api/types';

	interface Props {
		correction: PublicLogCorrectionResponse;
	}

	let { correction }: Props = $props();

	const queryClient = new QueryClient({
		defaultOptions: {
			queries: { retry: false },
			mutations: { retry: false }
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<CorrectionCard {correction} />
</QueryClientProvider>
