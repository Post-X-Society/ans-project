<script lang="ts">
	import { page } from '$app/stores';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { logout as apiLogout } from '$lib/api/auth';

	let currentPath = $derived($page.url.pathname);
	let auth = $derived($authStore);
	let showAdmin = $derived($isAdmin);

	async function handleLogout() {
		try {
			await apiLogout();
		} catch (error) {
			console.error('Logout error:', error);
		} finally {
			authStore.clearAuth();
			goto('/login');
		}
	}
</script>

<nav class="bg-white shadow">
	<div class="container mx-auto px-4">
		<div class="flex items-center justify-between py-4">
			<ul class="flex space-x-6">
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
				{#if auth.isAuthenticated}
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
							href="/submissions"
							class="text-gray-700 hover:text-primary-600 transition"
							class:font-bold={currentPath === '/submissions'}
							class:text-primary-600={currentPath === '/submissions'}
						>
							Submissions
						</a>
					</li>
				{/if}
				{#if showAdmin}
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
				{/if}
			</ul>

			<div class="flex items-center space-x-4">
				{#if auth.isAuthenticated && auth.user}
					<span class="text-sm text-gray-600">
						{auth.user.email}
						<span
							class="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
							class:bg-purple-100={auth.user.role === 'super_admin'}
							class:text-purple-800={auth.user.role === 'super_admin'}
							class:bg-blue-100={auth.user.role === 'admin'}
							class:text-blue-800={auth.user.role === 'admin'}
							class:bg-green-100={auth.user.role === 'reviewer'}
							class:text-green-800={auth.user.role === 'reviewer'}
							class:bg-gray-100={auth.user.role === 'submitter'}
							class:text-gray-800={auth.user.role === 'submitter'}
						>
							{auth.user.role}
						</span>
					</span>
					<button
						onclick={handleLogout}
						class="text-sm text-gray-700 hover:text-primary-600 transition font-medium"
					>
						Logout
					</button>
				{:else}
					<a
						href="/login"
						class="text-sm text-gray-700 hover:text-primary-600 transition font-medium"
					>
						Login
					</a>
					<a
						href="/register"
						class="text-sm bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition font-medium"
					>
						Register
					</a>
				{/if}
			</div>
		</div>
	</div>
</nav>
