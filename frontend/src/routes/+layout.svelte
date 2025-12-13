<script lang="ts">
	import '../app.css';
	import Header from '$lib/components/Header.svelte';
	import Nav from '$lib/components/Nav.svelte';
	import Footer from '$lib/components/Footer.svelte';
</script>

<div class="flex flex-col min-h-screen">
	<Header />
	<Nav />
	<main class="flex-1">
		<slot />
	</main>
	<Footer />
</div>
