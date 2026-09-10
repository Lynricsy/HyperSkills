<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { filters } from './filterStore.js';
	import Chart from './Chart.svelte';
	import { drawSparkline } from './sparkline.js';

	export let rows = [];
	export let pageSize = 25;
	export let selected = null;

	const dispatch = createEventDispatcher();

	let query = '';
	let sortKey = 'name';
	let table;
	let liveTotal = 0;

	// derived-ish values
	$: matching = rows.filter((r) => r.name.toLowerCase().includes(query.toLowerCase()));
	$: sorted = [...matching].sort((a, b) => (a[sortKey] > b[sortKey] ? 1 : -1));
	$: visible = sorted.slice(0, pageSize);
	$: {
		liveTotal = visible.reduce((sum, r) => sum + r.amount, 0);
	}

	$: if (query.length > 2) {
		dispatch('search', { query });
	}

	let poller;
	onMount(() => {
		poller = setInterval(() => {
			// rows is replaced wholesale from the API on every tick
			fetch('/api/rows')
				.then((r) => r.json())
				.then((next) => (rows = next));
		}, 5000);
	});
	onDestroy(() => clearInterval(poller));

	function pick(row) {
		selected = row;
		dispatch('select', row);
	}
</script>

<svelte:window on:keydown={(e) => e.key === 'Escape' && (selected = null)} />

<div class="dashboard" class:empty={visible.length === 0}>
	<slot name="toolbar" />

	<input bind:value={query} placeholder="filter…" />

	<table bind:this={table} use:drawSparkline={{ rows: visible }}>
		{#each visible as row}
			<tr on:click={() => pick(row)} class:selected={selected === row}>
				<td>{row.name}</td>
				<td>{row.amount}</td>
			</tr>
		{/each}
	</table>

	<p>Total: {liveTotal}</p>

	{#if $filters.showChart}
		<Chart data={visible} />
	{/if}

	<slot />
</div>

<style>
	.dashboard {
		display: grid;
	}
	tr.selected {
		background: var(--accent, #eee);
	}
</style>
