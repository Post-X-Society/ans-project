<script lang="ts">
	export interface Tab {
		id: string;
		label: string;
		hidden?: boolean;
		badge?: number;
	}

	interface Props {
		tabs: Tab[];
		activeTab: string;
		onTabChange?: (tabId: string) => void;
	}

	let { tabs, activeTab, onTabChange }: Props = $props();

	function handleTabClick(tabId: string) {
		if (tabId !== activeTab && onTabChange) {
			onTabChange(tabId);
		}
	}

	function handleKeyDown(event: KeyboardEvent, tabId: string) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleTabClick(tabId);
		}
	}

	// Filter out hidden tabs
	const visibleTabs = $derived(tabs.filter((tab) => !tab.hidden));
</script>

<div role="tablist" class="border-b border-gray-200">
	<nav class="flex space-x-8" aria-label="Tabs">
		{#each visibleTabs as tab}
			<button
				role="tab"
				type="button"
				aria-selected={activeTab === tab.id}
				onclick={() => handleTabClick(tab.id)}
				onkeydown={(e) => handleKeyDown(e, tab.id)}
				class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 {activeTab ===
				tab.id
					? 'border-primary-600 text-primary-600'
					: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
			>
				{tab.label}
				{#if tab.badge !== undefined && tab.badge > 0}
					<span
						class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {activeTab ===
						tab.id
							? 'bg-primary-100 text-primary-600'
							: 'bg-gray-100 text-gray-600'}"
					>
						{tab.badge}
					</span>
				{/if}
			</button>
		{/each}
	</nav>
</div>
