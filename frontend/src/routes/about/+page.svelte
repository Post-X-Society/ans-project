<!--
  About Index Page

  Issue #85: Frontend: Public Transparency Pages
  EPIC #51: Transparency & Methodology Pages

  Redirects to the first transparency page (methodology).
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/about/methodology', { replaceState: true });
	});
</script>

<div class="flex items-center justify-center py-12">
	<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
</div>
