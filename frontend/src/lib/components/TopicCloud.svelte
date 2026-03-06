<script lang="ts">
	import type { TopicNavItem } from '$lib/types';

	interface Props {
		topics: TopicNavItem[];
	}

	let { topics }: Props = $props();

	// Calculate font sizes based on post count
	const maxCount = $derived(Math.max(...topics.map((t) => t.post_count), 1));
	const minCount = $derived(Math.min(...topics.map((t) => t.post_count), 1));

	function getFontSize(count: number): number {
		const range = maxCount - minCount || 1;
		const normalized = (count - minCount) / range;
		// Scale from 0.75rem to 2rem
		return 0.75 + normalized * 1.25;
	}

	function getOpacity(count: number): number {
		const range = maxCount - minCount || 1;
		const normalized = (count - minCount) / range;
		// Scale from 0.5 to 1
		return 0.5 + normalized * 0.5;
	}
</script>

<div class="topic-cloud">
	<h3 class="cloud-title">Topic Cloud</h3>
	<div class="cloud-content">
		{#each topics as topic (topic.slug)}
			<a
				href="/topics/{topic.slug}"
				class="cloud-tag"
				style="font-size: {getFontSize(topic.post_count)}rem; opacity: {getOpacity(topic.post_count)};"
				title="{topic.name}: {topic.post_count} posts"
			>
				{topic.name}
			</a>
		{/each}
		{#if topics.length === 0}
			<div class="cloud-empty">No topics yet</div>
		{/if}
	</div>
</div>

<style>
	.topic-cloud {
		background: rgba(18, 18, 26, 0.8);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		transition: box-shadow 0.2s ease;
	}

	.topic-cloud:hover {
		box-shadow: 0 0 30px rgba(139, 92, 246, 0.15);
	}

	.cloud-title {
		font-size: var(--font-size-base);
		font-weight: var(--font-weight-semibold);
		margin: 0 0 var(--spacing-md) 0;
		color: var(--color-text-primary);
	}

	.cloud-content {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-sm);
		align-items: center;
		justify-content: center;
		min-height: 100px;
	}

	.cloud-tag {
		color: var(--color-accent);
		text-decoration: none;
		transition: all 0.2s ease;
		padding: var(--spacing-xs);
	}

	.cloud-tag:hover {
		color: var(--color-accent-secondary);
		transform: scale(1.1);
	}

	.cloud-empty {
		color: var(--color-text-muted);
		font-style: italic;
		width: 100%;
		text-align: center;
	}
</style>
