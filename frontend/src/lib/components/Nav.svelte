<script lang="ts">
	import { page } from '$app/stores';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import { logout as apiLogout } from '$lib/api/auth';
	import { t } from '$lib/i18n';
	import LanguageSelector from './LanguageSelector.svelte';

	let currentPath = $derived($page.url.pathname);
	let auth = $derived($authStore);
	let showAdmin = $derived($isAdmin);
	let showAdminDropdown = $state(false);

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

	function toggleAdminDropdown() {
		showAdminDropdown = !showAdminDropdown;
	}

	function closeAdminDropdown() {
		showAdminDropdown = false;
	}
</script>

<svelte:window onclick={closeAdminDropdown} />

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
						{$t('nav.home')}
					</a>
				</li>
				<li>
					<a
						href="/about"
						class="text-gray-700 hover:text-primary-600 transition"
						class:font-bold={currentPath.startsWith('/about')}
						class:text-primary-600={currentPath.startsWith('/about')}
					>
						{$t('nav.about')}
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
							{$t('nav.submit')}
						</a>
					</li>
					<li>
						<a
							href="/submissions"
							class="text-gray-700 hover:text-primary-600 transition"
							class:font-bold={currentPath === '/submissions'}
							class:text-primary-600={currentPath === '/submissions'}
						>
							{$t('nav.submissions')}
						</a>
					</li>
				{/if}
				{#if showAdmin}
					<li class="relative">
						<button
							onclick={(e) => {
								e.stopPropagation();
								toggleAdminDropdown();
							}}
							class="text-gray-700 hover:text-primary-600 transition inline-flex items-center"
							class:font-bold={currentPath.startsWith('/admin')}
							class:text-primary-600={currentPath.startsWith('/admin')}
						>
							{$t('nav.admin')}
							<svg
								class="ml-1 w-4 h-4 transition-transform"
								class:rotate-180={showAdminDropdown}
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 9l-7 7-7-7"
								/>
							</svg>
						</button>

						{#if showAdminDropdown}
							<div
								class="absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50"
								onclick={(e) => e.stopPropagation()}
							>
								<div class="py-1" role="menu">
									<a
										href="/admin"
										class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition"
										class:bg-gray-100={currentPath === '/admin'}
										onclick={closeAdminDropdown}
									>
										{$t('nav.userManagement')}
									</a>
									<a
										href="/admin/corrections"
										class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition"
										class:bg-gray-100={currentPath.startsWith('/admin/corrections')}
										onclick={closeAdminDropdown}
									>
										{$t('nav.corrections')}
									</a>
									<a
										href="/admin/transparency"
										class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition"
										class:bg-gray-100={currentPath.startsWith('/admin/transparency')}
										onclick={closeAdminDropdown}
									>
										{$t('nav.transparencyPages')}
									</a>
								</div>
							</div>
						{/if}
					</li>
				{/if}
			</ul>

			<div class="flex items-center space-x-4">
				<LanguageSelector />
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
						{$t('nav.logout')}
					</button>
				{:else}
					<a
						href="/login"
						class="text-sm text-gray-700 hover:text-primary-600 transition font-medium"
					>
						{$t('nav.login')}
					</a>
					<a
						href="/register"
						class="text-sm bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition font-medium"
					>
						{$t('nav.register')}
					</a>
				{/if}
			</div>
		</div>
	</div>
</nav>
