<script lang="ts">
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { register } from '$lib/api/auth';
	import { onMount } from 'svelte';

	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let errors = $state<{
		email?: string;
		password?: string;
		confirmPassword?: string;
		general?: string;
	}>({});
	let isLoading = $state(false);

	// Redirect if already authenticated
	onMount(() => {
		const unsubscribe = authStore.subscribe((state) => {
			if (state.isAuthenticated) {
				goto('/');
			}
		});
		return unsubscribe;
	});

	function validateForm(): boolean {
		errors = {};
		let isValid = true;

		if (!email || email.trim().length === 0) {
			errors.email = 'Email is required';
			isValid = false;
		} else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
			errors.email = 'Please enter a valid email address';
			isValid = false;
		}

		if (!password || password.trim().length === 0) {
			errors.password = 'Password is required';
			isValid = false;
		} else if (password.length < 8) {
			errors.password = 'Password must be at least 8 characters';
			isValid = false;
		}

		if (password !== confirmPassword) {
			errors.confirmPassword = 'Passwords do not match';
			isValid = false;
		}

		return isValid;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();

		if (!validateForm()) {
			return;
		}

		isLoading = true;
		errors = {};

		try {
			const response = await register({ email, password });
			authStore.setAuth(response.user, response.access_token, response.refresh_token);
			goto('/submit');
		} catch (error: any) {
			console.error('Registration error:', error);
			if (error.response?.status === 400) {
				errors.general = 'Email already registered or invalid data';
			} else if (error.response?.data?.detail) {
				errors.general = error.response.data.detail;
			} else {
				errors.general = 'An error occurred during registration. Please try again.';
			}
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
	<div class="max-w-md w-full space-y-8">
		<div>
			<h2 class="mt-6 text-center text-3xl font-bold text-gray-900">Create your account</h2>
			<p class="mt-2 text-center text-sm text-gray-600">
				Already have an account?
				<a href="/login" class="font-medium text-primary-600 hover:text-primary-500">
					Sign in here
				</a>
			</p>
		</div>

		<form class="mt-8 space-y-6" onsubmit={handleSubmit}>
			{#if errors.general}
				<div class="bg-red-50 border border-red-200 rounded-lg p-4">
					<p class="text-red-800 text-sm">{errors.general}</p>
				</div>
			{/if}

			<div class="space-y-4">
				<div>
					<label for="email" class="block text-sm font-medium text-gray-700 mb-1">
						Email address
					</label>
					<input
						id="email"
						name="email"
						type="email"
						autocomplete="email"
						bind:value={email}
						class="appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
						class:border-red-500={errors.email}
						placeholder="you@example.com"
					/>
					{#if errors.email}
						<p class="mt-1 text-sm text-red-600">{errors.email}</p>
					{/if}
				</div>

				<div>
					<label for="password" class="block text-sm font-medium text-gray-700 mb-1">
						Password
					</label>
					<input
						id="password"
						name="password"
						type="password"
						autocomplete="new-password"
						bind:value={password}
						class="appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
						class:border-red-500={errors.password}
						placeholder="Minimum 8 characters"
					/>
					{#if errors.password}
						<p class="mt-1 text-sm text-red-600">{errors.password}</p>
					{/if}
				</div>

				<div>
					<label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-1">
						Confirm Password
					</label>
					<input
						id="confirmPassword"
						name="confirmPassword"
						type="password"
						autocomplete="new-password"
						bind:value={confirmPassword}
						class="appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
						class:border-red-500={errors.confirmPassword}
						placeholder="Re-enter your password"
					/>
					{#if errors.confirmPassword}
						<p class="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
					{/if}
				</div>
			</div>

			<div>
				<button
					type="submit"
					disabled={isLoading}
					class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
				>
					{#if isLoading}
						Creating account...
					{:else}
						Create account
					{/if}
				</button>
			</div>

			<div class="text-center text-xs text-gray-500">
				By creating an account, you will be assigned the SUBMITTER role.
			</div>
		</form>
	</div>
</div>
