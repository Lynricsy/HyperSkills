<!-- src/routes/+layout.svelte -->
<script lang="ts">
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { page } from '$app/state';

	let { children } = $props();
	let sending = $state(false);
</script>

{@render children()}

<footer>
	<form
		method="POST"
		action="/newsletter?/subscribe"
		use:enhance={() => {
			sending = true;
			return async ({ update }) => {
				await update();
				await invalidateAll();
				sending = false;
			};
		}}
	>
		<label>
			Newsletter
			<input name="email" type="email" value={page.form?.email ?? ''} />
		</label>
		{#if page.form?.invalid}<p class="error">Enter a valid email address</p>{/if}
		{#if page.form?.subscribed}<p>Thanks, you're on the list.</p>{/if}
		<button disabled={sending}>Subscribe</button>
	</form>
</footer>
