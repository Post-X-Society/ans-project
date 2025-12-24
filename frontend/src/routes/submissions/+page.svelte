<script lang="ts">
	import { authStore } from '$lib/stores/auth';
	import { t } from '$lib/i18n';
	import SubmissionsList from '$lib/components/submissions/SubmissionsList.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	let auth = $derived($authStore);

	/**
	 * Get role-specific welcome message using i18n
	 */
	function getWelcomeMessage(role: string): string {
		const roleKey = role === 'super_admin' ? 'superAdmin' : role;
		return $t(`roleMessages.${roleKey}`) || $t('roleMessages.default');
	}

	/**
	 * Get role badge styling
	 */
	function getRoleBadgeClasses(role: string): string {
		const baseClasses = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium';
		switch (role) {
			case 'super_admin':
				return `${baseClasses} bg-purple-100 text-purple-800`;
			case 'admin':
				return `${baseClasses} bg-blue-100 text-blue-800`;
			case 'reviewer':
				return `${baseClasses} bg-green-100 text-green-800`;
			case 'submitter':
				return `${baseClasses} bg-gray-100 text-gray-800`;
			default:
				return baseClasses;
		}
	}

	/**
	 * Get translated role name
	 */
	function getRoleName(role: string): string {
		switch (role) {
			case 'super_admin':
				return $t('roles.superAdmin');
			case 'admin':
				return $t('roles.admin');
			case 'reviewer':
				return $t('roles.reviewer');
			case 'submitter':
				return $t('roles.submitter');
			default:
				return role;
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-7xl mx-auto">
		<!-- Page Header -->
		<div class="mb-8">
			<div class="flex items-center justify-between mb-4">
				<h1 class="text-3xl font-bold text-gray-900">{$t('submissions.title')}</h1>
				{#if auth.user}
					<span class={getRoleBadgeClasses(auth.user.role)}>
						{getRoleName(auth.user.role).toUpperCase()}
					</span>
				{/if}
			</div>

			<p class="text-gray-600">
				{auth.user ? getWelcomeMessage(auth.user.role) : $t('roleMessages.default')}
			</p>

			<!-- Quick Actions -->
			<div class="mt-4 flex flex-wrap gap-3">
				<a
					href="/submit"
					class="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
				>
					<svg
						class="w-5 h-5 mr-2"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
					{$t('submissions.newSubmission')}
				</a>

				{#if auth.user && (auth.user.role === 'admin' || auth.user.role === 'super_admin')}
					<a
						href="/admin"
						class="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium"
					>
						<svg
							class="w-5 h-5 mr-2"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
							/>
						</svg>
						{$t('admin.adminPanel')}
					</a>
				{/if}
			</div>
		</div>

		<!-- Submissions List Component -->
		<SubmissionsList initialData={data.submissions} />
	</div>
</div>
