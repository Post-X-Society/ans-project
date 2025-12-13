<script lang="ts">
	// Footer component - uses Svelte 5 runes
	let currentYear = $state(new Date().getFullYear());
</script>

<footer class="bg-gray-800 text-white mt-auto">
	<div class="container mx-auto px-4 py-6">
		<div class="flex flex-col md:flex-row justify-between items-center">
			<div class="mb-4 md:mb-0">
				<p class="text-sm text-gray-300">© {currentYear} Ans. All rights reserved.</p>
			</div>
			<nav class="flex space-x-6">
				<a href="/privacy" class="text-sm text-gray-300 hover:text-white transition">Privacy</a>
				<a href="/terms" class="text-sm text-gray-300 hover:text-white transition">Terms</a>
				<a href="/contact" class="text-sm text-gray-300 hover:text-white transition">Contact</a>
			</nav>
		</div>
	</div>
</footer>
