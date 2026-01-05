<script lang="ts">
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import CorrectionReviewDashboard from '../CorrectionReviewDashboard.svelte';

	interface Props {
		onReviewComplete?: () => void;
	}

	let { onReviewComplete }: Props = $props();

	const queryClient = new QueryClient({
		defaultOptions: {
			queries: { retry: false },
			mutations: { retry: false }
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<CorrectionReviewDashboard {onReviewComplete} />
</QueryClientProvider>
