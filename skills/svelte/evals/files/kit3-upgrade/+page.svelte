<!-- src/routes/account/[id]/+page.svelte -->
<script lang="ts">
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { enhance } from '$app/forms';
	import { getUsage } from './usage.remote';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const usage = $derived(await getUsage(data.account.id));
</script>

<h1>{data.account.name}</h1>
<p>Plan: {data.account.plan} · {$page.url.pathname}</p>

{#if browser}
	<p>Your local time: {new Date().toLocaleTimeString()}</p>
{/if}

<p>API calls this month: {usage.calls}</p>

<ul>
	{#each data.invoices as invoice (invoice.id)}
		<li>{invoice.issuedAt.toLocaleDateString()}: {invoice.total}</li>
	{/each}
</ul>

<form method="POST" action="?/theme" use:enhance>
	<select name="theme" value={data.theme}>
		<option value="light">Light</option>
		<option value="dark">Dark</option>
	</select>
	<button>Save</button>
</form>
