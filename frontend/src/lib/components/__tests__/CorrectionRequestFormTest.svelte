<script lang="ts">
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import CorrectionRequestForm from '../CorrectionRequestForm.svelte';

	interface Props {
		factCheckId?: string;
		onSuccess?: () => void;
	}

	let { factCheckId = 'test-fact-check-id', onSuccess }: Props = $props();

	const queryClient = new QueryClient({
		defaultOptions: {
			queries: { retry: false },
			mutations: { retry: false }
		}
	});
</script>

<QueryClientProvider client={queryClient}>
	<CorrectionRequestForm {factCheckId} {onSuccess} />
</QueryClientProvider>
