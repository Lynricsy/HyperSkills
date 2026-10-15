<script lang="ts">
	import { getArticle } from './article.remote';
	import ReadingTime from './ReadingTime.svelte';

	let { slug }: { slug: string } = $props();

	const article = $derived(await getArticle(slug));
</script>

<article>
	<h1>{article.title}</h1>
	<p class="byline">{article.author}</p>

	<!-- ReadingTime kept showing the previous article's value after client-side
	     navigation between articles, so it is re-created whenever the article changes. -->
	{#key article.id}
		<ReadingTime text={article.body} />
	{/key}

	{@html article.html}
</article>
