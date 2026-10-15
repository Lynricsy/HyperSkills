<script lang="ts">
	import { page } from '$app/state';
	import Article from './Article.svelte';
	import ArticleSkeleton from './ArticleSkeleton.svelte';
	import Comments from './Comments.svelte';
</script>

<svelte:boundary>
	{#snippet pending()}
		<ArticleSkeleton />
	{/snippet}

	<Article slug={page.params.slug!} />
	<Comments slug={page.params.slug!} />
</svelte:boundary>
