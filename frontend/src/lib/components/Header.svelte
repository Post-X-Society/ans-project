<script lang="ts">
	import { authStore } from '$lib/stores/auth';

	let auth = $derived($authStore);
</script>

<header class="bg-primary-600 text-white shadow-md">
	<div class="container mx-auto px-4 py-4">
		<div class="flex items-center justify-between">
			<div>
				<a href="/" class="hover:opacity-90 transition">
					<h1 class="text-2xl font-bold">Ans</h1>
					<p class="text-sm text-primary-100">Community based fact-checking for SnapChat</p>
				</a>
			</div>
			{#if auth.isAuthenticated && auth.user}
				<div class="text-right">
					<p class="text-sm text-primary-100">Welcome back,</p>
					<p class="font-medium">{auth.user.email}</p>
				</div>
			{/if}
		</div>
	</div>
</header>
