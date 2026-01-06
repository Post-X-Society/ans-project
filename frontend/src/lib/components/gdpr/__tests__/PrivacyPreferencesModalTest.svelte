<!--
  Test Wrapper for PrivacyPreferencesModal
  Issue #93: Frontend: Cookie Consent & GDPR Banners (TDD)

  Provides test context for the PrivacyPreferencesModal component.
-->
<script lang="ts">
	import PrivacyPreferencesModal from '../PrivacyPreferencesModal.svelte';

	interface Props {
		open?: boolean;
		onClose?: () => void;
	}

	let { open = false, onClose = () => {} }: Props = $props();
</script>

<PrivacyPreferencesModal {open} {onClose} />
