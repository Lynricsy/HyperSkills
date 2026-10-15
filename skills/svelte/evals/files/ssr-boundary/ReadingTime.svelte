<script lang="ts">
	let { text }: { text: string } = $props();

	const words = text.trim().split(/\s+/).length;
	const minutes = Math.max(1, Math.round(words / 230));
	const label = minutes === 1 ? '1 minute read' : `${minutes} minute read`;
</script>

<span class="reading-time">{label}</span>
