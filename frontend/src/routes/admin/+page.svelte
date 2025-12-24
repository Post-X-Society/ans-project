<script lang="ts">
	import { onMount } from 'svelte';
	import { authStore, isSuperAdmin } from '$lib/stores/auth';
	import { t, getCurrentLocale } from '$lib/i18n';
	import { getUsers, createUser, updateUserRole, updateUser } from '$lib/api/users';
	import type { User, UserRole } from '$lib/api/types';

	let users = $state<User[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let showCreateModal = $state(false);
	let isSuperAdminUser = $derived($isSuperAdmin);

	// Create user form
	let newUserEmail = $state('');
	let newUserPassword = $state('');
	let newUserRole = $state<UserRole>('submitter');
	let createError = $state<string | null>(null);
	let isCreating = $state(false);

	// Edit user state
	let editingUserId = $state<string | null>(null);
	let editUserRole = $state<UserRole>('submitter');
	let editUserActive = $state(true);

	onMount(() => {
		loadUsers();
	});

	async function loadUsers() {
		isLoading = true;
		error = null;
		try {
			users = await getUsers();
		} catch (err: any) {
			console.error('Error loading users:', err);
			error = err.response?.data?.detail || $t('errors.loadFailed');
		} finally {
			isLoading = false;
		}
	}

	async function handleCreateUser(e: Event) {
		e.preventDefault();
		if (!newUserEmail || !newUserPassword) return;

		isCreating = true;
		createError = null;

		try {
			await createUser({
				email: newUserEmail,
				password: newUserPassword,
				role: newUserRole
			});
			showCreateModal = false;
			newUserEmail = '';
			newUserPassword = '';
			newUserRole = 'submitter';
			await loadUsers();
		} catch (err: any) {
			console.error('Error creating user:', err);
			createError = err.response?.data?.detail || $t('errors.saveFailed');
		} finally {
			isCreating = false;
		}
	}

	async function handleUpdateRole(userId: string, role: UserRole) {
		try {
			await updateUserRole(userId, role);
			await loadUsers();
			editingUserId = null;
		} catch (err: any) {
			console.error('Error updating role:', err);
			alert(err.response?.data?.detail || $t('errors.saveFailed'));
		}
	}

	async function handleToggleActive(userId: string, isActive: boolean) {
		try {
			await updateUser(userId, { is_active: !isActive });
			await loadUsers();
		} catch (err: any) {
			console.error('Error updating user:', err);
			alert(err.response?.data?.detail || $t('errors.saveFailed'));
		}
	}

	function startEditRole(userId: string, currentRole: UserRole, currentActive: boolean) {
		editingUserId = userId;
		editUserRole = currentRole;
		editUserActive = currentActive;
	}

	function cancelEdit() {
		editingUserId = null;
	}

	function getRoleBadgeClass(role: UserRole): string {
		const baseClass = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
		switch (role) {
			case 'super_admin':
				return `${baseClass} bg-purple-100 text-purple-800`;
			case 'admin':
				return `${baseClass} bg-blue-100 text-blue-800`;
			case 'reviewer':
				return `${baseClass} bg-green-100 text-green-800`;
			case 'submitter':
				return `${baseClass} bg-gray-100 text-gray-800`;
			default:
				return baseClass;
		}
	}

	function getRoleName(role: UserRole): string {
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

	function formatDate(dateString: string): string {
		const locale = getCurrentLocale();
		return new Date(dateString).toLocaleDateString(locale === 'nl' ? 'nl-NL' : 'en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-6xl mx-auto">
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold text-gray-900">{$t('admin.title')}</h1>
			<button
				onclick={() => (showCreateModal = true)}
				class="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition font-medium"
			>
				{$t('admin.createUser')}
			</button>
		</div>

		{#if isLoading}
			<div class="text-center py-12">
				<p class="text-gray-600">{$t('admin.loadingUsers')}</p>
			</div>
		{:else if error}
			<div class="bg-red-50 border border-red-200 rounded-lg p-4">
				<p class="text-red-800">{error}</p>
			</div>
		{:else if users.length === 0}
			<div class="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
				<p class="text-gray-600">{$t('admin.noUsersFound')}</p>
			</div>
		{:else}
			<div class="bg-white shadow overflow-hidden sm:rounded-lg">
				<table class="min-w-full divide-y divide-gray-200">
					<thead class="bg-gray-50">
						<tr>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
							>
								{$t('admin.email')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
							>
								{$t('admin.role')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
							>
								{$t('admin.status')}
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
							>
								{$t('admin.created')}
							</th>
							<th
								class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
							>
								{$t('admin.actions')}
							</th>
						</tr>
					</thead>
					<tbody class="bg-white divide-y divide-gray-200">
						{#each users as user (user.id)}
							<tr>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
									{user.email}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm">
									{#if editingUserId === user.id}
										<select
											bind:value={editUserRole}
											class="border border-gray-300 rounded px-2 py-1 text-sm"
										>
											<option value="submitter">{getRoleName('submitter')}</option>
											<option value="reviewer">{getRoleName('reviewer')}</option>
											<option value="admin">{getRoleName('admin')}</option>
											{#if isSuperAdminUser}
												<option value="super_admin">{getRoleName('super_admin')}</option>
											{/if}
										</select>
									{:else}
										<span class={getRoleBadgeClass(user.role)}>{getRoleName(user.role)}</span>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm">
									{#if user.is_active}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
										>
											{$t('status.active')}
										</span>
									{:else}
										<span
											class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
										>
											{$t('status.inactive')}
										</span>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDate(user.created_at)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									{#if editingUserId === user.id}
										<button
											onclick={() => handleUpdateRole(user.id, editUserRole)}
											class="text-green-600 hover:text-green-900 mr-3"
										>
											{$t('common.save')}
										</button>
										<button
											onclick={cancelEdit}
											class="text-gray-600 hover:text-gray-900"
										>
											{$t('common.cancel')}
										</button>
									{:else}
										<button
											onclick={() => startEditRole(user.id, user.role, user.is_active)}
											class="text-primary-600 hover:text-primary-900 mr-3"
										>
											{$t('admin.editRole')}
										</button>
										<button
											onclick={() => handleToggleActive(user.id, user.is_active)}
											class="text-orange-600 hover:text-orange-900"
										>
											{user.is_active ? $t('admin.deactivate') : $t('admin.activate')}
										</button>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<!-- Create User Modal -->
{#if showCreateModal}
	<div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
		<div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
			<div class="px-6 py-4 border-b border-gray-200">
				<h2 class="text-xl font-bold text-gray-900">{$t('admin.createNewUser')}</h2>
			</div>

			<form onsubmit={handleCreateUser} class="px-6 py-4 space-y-4">
				{#if createError}
					<div class="bg-red-50 border border-red-200 rounded-lg p-3">
						<p class="text-red-800 text-sm">{createError}</p>
					</div>
				{/if}

				<div>
					<label for="new-email" class="block text-sm font-medium text-gray-700 mb-1">
						{$t('admin.email')}
					</label>
					<input
						id="new-email"
						type="email"
						bind:value={newUserEmail}
						required
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
						placeholder={$t('auth.emailPlaceholder')}
					/>
				</div>

				<div>
					<label for="new-password" class="block text-sm font-medium text-gray-700 mb-1">
						{$t('auth.password')}
					</label>
					<input
						id="new-password"
						type="password"
						bind:value={newUserPassword}
						required
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
						placeholder={$t('auth.passwordMinChars')}
					/>
				</div>

				<div>
					<label for="new-role" class="block text-sm font-medium text-gray-700 mb-1">
						{$t('admin.role')}
					</label>
					<select
						id="new-role"
						bind:value={newUserRole}
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
					>
						<option value="submitter">{getRoleName('submitter')}</option>
						<option value="reviewer">{getRoleName('reviewer')}</option>
						<option value="admin">{getRoleName('admin')}</option>
						{#if isSuperAdminUser}
							<option value="super_admin">{getRoleName('super_admin')}</option>
						{/if}
					</select>
				</div>

				<div class="flex justify-end space-x-3 pt-4">
					<button
						type="button"
						onclick={() => (showCreateModal = false)}
						class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
					>
						{$t('common.cancel')}
					</button>
					<button
						type="submit"
						disabled={isCreating}
						class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 transition"
					>
						{isCreating ? $t('admin.creatingUser') : $t('admin.createUser')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
