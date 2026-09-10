<script lang="ts">
	import { invalidate } from '$app/navigation';
	import { page } from '$app/stores';

	export let data;

	let refreshing = false;

	async function refresh() {
		refreshing = true;
		await invalidate('/api/exchange-rates');
		refreshing = false;
	}
</script>

<h1>{data.team.name} — {$page.url.pathname}</h1>

<p>Generated {data.generatedAt.toLocaleString(data.locale)}</p>

<button on:click={refresh} disabled={refreshing}>Refresh rates</button>

<ul>
	{#each data.invoices as invoice}
		<li>{invoice.reference} — {invoice.total()} ({data.rates.get(invoice.currency)})</li>
	{/each}
</ul>
