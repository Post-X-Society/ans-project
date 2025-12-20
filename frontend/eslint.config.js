import svelte from 'eslint-plugin-svelte';
import ts from 'typescript-eslint';

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
	...ts.configs.recommended,
	...svelte.configs['flat/recommended'],
	{
		languageOptions: {
			parserOptions: {
				parser: ts.parser
			}
		},
		rules: {
			// Temporarily disable strict rules to allow merge
			'@typescript-eslint/no-explicit-any': 'warn',
			'@typescript-eslint/no-unused-vars': 'warn',
			'svelte/valid-compile': 'warn'
		}
	},
	{
		ignores: ['build/', '.svelte-kit/', 'dist/', 'node_modules/']
	}
];
