import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { User } from '$lib/api/types';

interface AuthState {
	user: User | null;
	accessToken: string | null;
	refreshToken: string | null;
	isAuthenticated: boolean;
	isLoading: boolean;
}

const STORAGE_KEY_ACCESS = 'ans_access_token';
const STORAGE_KEY_REFRESH = 'ans_refresh_token';
const STORAGE_KEY_USER = 'ans_user';

// Initialize state from localStorage if in browser
function getInitialState(): AuthState {
	if (!browser) {
		return {
			user: null,
			accessToken: null,
			refreshToken: null,
			isAuthenticated: false,
			isLoading: true
		};
	}

	const accessToken = localStorage.getItem(STORAGE_KEY_ACCESS);
	const refreshToken = localStorage.getItem(STORAGE_KEY_REFRESH);
	const userStr = localStorage.getItem(STORAGE_KEY_USER);

	// Parse user data safely, handling null, undefined, or invalid JSON
	let user = null;
	if (userStr && userStr !== 'undefined' && userStr !== 'null') {
		try {
			user = JSON.parse(userStr);
		} catch (e) {
			console.error('Failed to parse user data from localStorage:', e);
			localStorage.removeItem(STORAGE_KEY_USER);
		}
	}

	return {
		user,
		accessToken,
		refreshToken,
		isAuthenticated: !!accessToken && !!user,
		isLoading: false
	};
}

// Create the auth store
function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(getInitialState());

	return {
		subscribe,

		// Set user and tokens after login
		setAuth(user: User, accessToken: string, refreshToken: string) {
			if (browser) {
				localStorage.setItem(STORAGE_KEY_ACCESS, accessToken);
				localStorage.setItem(STORAGE_KEY_REFRESH, refreshToken);
				localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
			}

			update((state) => ({
				...state,
				user,
				accessToken,
				refreshToken,
				isAuthenticated: true,
				isLoading: false
			}));
		},

		// Update access token after refresh
		updateAccessToken(accessToken: string) {
			if (browser) {
				localStorage.setItem(STORAGE_KEY_ACCESS, accessToken);
			}

			update((state) => ({
				...state,
				accessToken
			}));
		},

		// Clear auth state on logout
		clearAuth() {
			if (browser) {
				localStorage.removeItem(STORAGE_KEY_ACCESS);
				localStorage.removeItem(STORAGE_KEY_REFRESH);
				localStorage.removeItem(STORAGE_KEY_USER);
			}

			set({
				user: null,
				accessToken: null,
				refreshToken: null,
				isAuthenticated: false,
				isLoading: false
			});
		},

		// Set loading state
		setLoading(isLoading: boolean) {
			update((state) => ({
				...state,
				isLoading
			}));
		},

		// Initialize from storage (call on app mount)
		initialize() {
			update((state) => ({
				...state,
				isLoading: false
			}));
		}
	};
}

export const authStore = createAuthStore();

// Derived stores for convenience
export const currentUser = derived(authStore, ($auth) => $auth.user);
export const isAuthenticated = derived(authStore, ($auth) => $auth.isAuthenticated);
export const isAdmin = derived(
	authStore,
	($auth) => $auth.user?.role === 'ADMIN' || $auth.user?.role === 'SUPER_ADMIN'
);
export const isSuperAdmin = derived(authStore, ($auth) => $auth.user?.role === 'SUPER_ADMIN');
