<script>
	import DataList from './DataList.svelte';

	let { users, onselect } = $props();
</script>

<DataList items={users} emptyText="No users yet" let:item let:index>
	{#snippet children()}
		<button type="button" onclick={() => onselect(item.id)}>
			{index + 1}. {item.name}
		</button>
	{/snippet}
</DataList>
