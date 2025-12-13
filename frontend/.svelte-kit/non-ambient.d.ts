
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/__tests__" | "/admin" | "/admin/__tests__" | "/submit" | "/submit/__tests__";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/__tests__": Record<string, never>;
			"/admin": Record<string, never>;
			"/admin/__tests__": Record<string, never>;
			"/submit": Record<string, never>;
			"/submit/__tests__": Record<string, never>
		};
		Pathname(): "/" | "/__tests__" | "/__tests__/" | "/admin" | "/admin/" | "/admin/__tests__" | "/admin/__tests__/" | "/submit" | "/submit/" | "/submit/__tests__" | "/submit/__tests__/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}