<script lang="ts">
	let { start = 0, onsave }: { start?: number; onsave?: (n: number) => void } = $props();

	let count = $state(start);
</script>

<button onclick={() => count++}>Increment: {count}</button>
<button onclick={() => onsave?.(count)}>Save draft</button>
