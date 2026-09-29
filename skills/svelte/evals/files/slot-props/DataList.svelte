<script>
	export let items = [];
	export let emptyText = 'Nothing here';
</script>

{#if items.length === 0}
	<p class="empty">{emptyText}</p>
{:else}
	<ul>
		{#each items as row, i (row.id)}
			<li class:odd={i % 2 === 1}>
				<slot item={row} index={i} />
			</li>
		{/each}
	</ul>
{/if}

<style>
	.odd {
		background: #f6f6f6;
	}
</style>
