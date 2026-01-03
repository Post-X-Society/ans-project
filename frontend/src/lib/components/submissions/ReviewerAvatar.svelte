<script lang="ts">
	interface Props {
		name?: string;
		email?: string;
		size?: 'sm' | 'md' | 'lg';
	}

	let { name, email, size = 'md' }: Props = $props();

	/**
	 * Generate initials from name or email
	 */
	function generateInitials(nameOrEmail: string): string {
		// If it's an email address, extract the part before @
		if (nameOrEmail.includes('@')) {
			const emailPart = nameOrEmail.split('@')[0];
			// Split by dots and hyphens
			const parts = emailPart.split(/[.\-_]/);
			if (parts.length >= 2) {
				return (parts[0][0] + parts[1][0]).toUpperCase();
			}
			return emailPart[0].toUpperCase();
		}

		// For regular names, take first letter of first and last word
		const words = nameOrEmail.trim().split(/\s+/);
		if (words.length >= 2) {
			return (words[0][0] + words[words.length - 1][0]).toUpperCase();
		}
		return words[0][0].toUpperCase();
	}

	/**
	 * Generate consistent background color from string hash
	 */
	function generateColor(str: string): string {
		// Simple hash function
		let hash = 0;
		for (let i = 0; i < str.length; i++) {
			hash = str.charCodeAt(i) + ((hash << 5) - hash);
		}

		// Generate HSL color with good saturation and lightness for readability
		const hue = Math.abs(hash % 360);
		return `hsl(${hue}, 65%, 50%)`;
	}

	/**
	 * Get size classes based on size prop
	 */
	function getSizeClasses(s: 'sm' | 'md' | 'lg'): string {
		switch (s) {
			case 'sm':
				return 'w-6 h-6 text-xs';
			case 'md':
				return 'w-8 h-8 text-sm';
			case 'lg':
				return 'w-10 h-10 text-base';
		}
	}

	const displayText = $derived(name || email || '?');
	const initials = $derived(generateInitials(displayText));
	const bgColor = $derived(generateColor(displayText));
	const sizeClasses = $derived(getSizeClasses(size));
</script>

<div
	data-testid="reviewer-avatar"
	role="img"
	aria-label="Reviewer: {displayText}"
	title={displayText}
	class="inline-flex items-center justify-center rounded-full font-semibold text-white {sizeClasses}"
	style="background-color: {bgColor}"
>
	{initials}
</div>
