<script lang="ts">
	import { locale, t } from '$lib/i18n';
	import { setLocale, SUPPORTED_LOCALES, LOCALE_NAMES, type SupportedLocale } from '$lib/i18n';

	let currentLocale = $derived($locale as SupportedLocale);

	function handleChange(event: Event) {
		const target = event.target as HTMLSelectElement;
		const newLocale = target.value as SupportedLocale;
		setLocale(newLocale);
	}
</script>

<div class="relative inline-block">
	<label for="language-select" class="sr-only">{$t('language.select')}</label>
	<select
		id="language-select"
		value={currentLocale}
		onchange={handleChange}
		class="appearance-none bg-transparent border border-gray-300 rounded-md pl-3 pr-8 py-1.5 text-sm text-gray-700 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
	>
		{#each SUPPORTED_LOCALES as loc}
			<option value={loc}>{LOCALE_NAMES[loc]}</option>
		{/each}
	</select>
	<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
		<svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</div>
</div>
