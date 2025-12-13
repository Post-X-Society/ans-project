import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	resolve: {
		conditions: ['browser']
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		globals: true,
		environment: 'jsdom',
		setupFiles: ['./src/__tests__/setup.ts'],
		alias: {
			$lib: '/src/lib'
		},
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html'],
			exclude: [
				'node_modules/',
				'src/__tests__/',
				'**/*.config.{js,ts}',
				'**/types.ts'
			]
		}
	},
	server: {
		host: '0.0.0.0',
		port: 5173,
		hmr: {
			overlay: true
		}
	},
	ssr: {
		noExternal: ['@tanstack/svelte-query']
	}
});
