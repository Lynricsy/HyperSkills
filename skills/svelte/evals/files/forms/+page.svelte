<script lang="ts">
	import { goto } from '$app/navigation';

	export let data;

	let email = data.lastEmail;
	let password = '';
	let errorMessage = '';
	let busy = false;

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		busy = true;
		errorMessage = '';

		const res = await fetch('?/login', {
			method: 'POST',
			body: new URLSearchParams({ email, password })
		});

		if (res.ok) {
			await goto('/dashboard');
		} else {
			errorMessage = 'Login failed';
		}
		busy = false;
	}
</script>

<form on:submit={submit}>
	<input name="email" type="email" bind:value={email} />
	<input name="password" type="password" bind:value={password} />

	{#if errorMessage}<p class="error">{errorMessage}</p>{/if}

	<button disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
</form>

<form method="GET" action="?/logout" use:enhance>
	<button>Sign out</button>
</form>
