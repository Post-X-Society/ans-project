<script lang="ts">
	// Nav component - uses Svelte 5 runes
	let currentPath = $state('/');
</script>

<nav class="bg-white shadow">
	<div class="container mx-auto px-4">
		<ul class="flex space-x-6 py-4">
			<li>
				<a
					href="/"
					class="text-gray-700 hover:text-primary-600 transition"
					class:font-bold={currentPath === '/'}
					class:text-primary-600={currentPath === '/'}
				>
					Home
				</a>
			</li>
			<li>
				<a
					href="/submit"
					class="text-gray-700 hover:text-primary-600 transition"
					class:font-bold={currentPath === '/submit'}
					class:text-primary-600={currentPath === '/submit'}
				>
					Submit
				</a>
			</li>
			<li>
				<a
					href="/admin"
					class="text-gray-700 hover:text-primary-600 transition"
					class:font-bold={currentPath === '/admin'}
					class:text-primary-600={currentPath === '/admin'}
				>
					Admin
				</a>
			</li>
		</ul>
	</div>
</nav>
