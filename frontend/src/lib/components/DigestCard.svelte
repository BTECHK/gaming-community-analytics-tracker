<script lang="ts">
	import type { Topic } from '$lib/types';
	import SentimentBar from './SentimentBar.svelte';
	import ConfidenceIndicator from './ConfidenceIndicator.svelte';
	import FeedbackButtons from './FeedbackButtons.svelte';
	import ReportModal from './ReportModal.svelte';

	interface Props {
		topic: Topic;
	}

	let { topic }: Props = $props();
	let reportModalOpen = $state(false);

	/** Check if topic was updated in the last 24 hours */
	const isNewToday = $derived(() => {
		if (!topic.period.end) return false;
		const endDate = new Date(topic.period.end);
		const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
		return endDate > oneDayAgo;
	});

	/** Truncate summary to 150 characters */
	const summaryExcerpt = $derived(() => {
		if (!topic.summary) return 'No summary available';
		return topic.summary.length > 150
			? topic.summary.slice(0, 147) + '...'
			: topic.summary;
	});
</script>

<article class="digest-card">
	<div class="card-header">
		<a href="/topics/{topic.slug}" class="topic-link">
			<h3 class="topic-name">{topic.name}</h3>
		</a>
		{#if isNewToday()}
			<span class="new-badge">New</span>
		{/if}
	</div>

	<p class="summary-excerpt">{summaryExcerpt()}</p>

	<div class="sentiment-compact">
		<SentimentBar sentiment={topic.sentiment} height={16} />
	</div>

	<div class="card-footer">
		<ConfidenceIndicator confidence={topic.confidence} showLabel={false} />
		<span class="post-count">{topic.post_count} posts</span>
		<a href="/topics/{topic.slug}" class="view-link">View details →</a>
	</div>

	<div class="card-feedback">
		<FeedbackButtons slug={topic.slug} onReport={() => reportModalOpen = true} />
	</div>
</article>

<ReportModal
	slug={topic.slug}
	topicName={topic.name}
	open={reportModalOpen}
	onClose={() => reportModalOpen = false}
/>

<style>
	.digest-card {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-md);
		transition: all 0.2s ease;
	}

	.digest-card:hover {
		border-color: var(--color-border-hover);
		background: var(--color-bg-card-hover);
	}

	.card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-sm);
	}

	.topic-link {
		text-decoration: none;
		color: inherit;
	}

	.topic-link:hover .topic-name {
		color: var(--color-accent);
	}

	.topic-name {
		font-size: var(--font-size-md);
		font-weight: var(--font-weight-semibold);
		color: var(--color-text-primary);
		margin: 0;
		transition: color 0.2s ease;
	}

	.new-badge {
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		background: var(--color-accent);
		color: white;
		padding: 2px 8px;
		border-radius: var(--radius-full);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.summary-excerpt {
		font-size: var(--font-size-sm);
		color: var(--color-text-secondary);
		line-height: 1.5;
		margin: 0 0 var(--spacing-sm) 0;
	}

	.sentiment-compact {
		margin-bottom: var(--spacing-sm);
	}

	.card-footer {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.post-count {
		background: var(--color-bg-secondary);
		padding: 2px 8px;
		border-radius: var(--radius-full);
	}

	.view-link {
		margin-left: auto;
		color: var(--color-accent);
		text-decoration: none;
		font-weight: var(--font-weight-medium);
	}

	.view-link:hover {
		text-decoration: underline;
	}

	.card-feedback {
		margin-top: var(--spacing-sm);
		padding-top: var(--spacing-sm);
		border-top: 1px solid var(--color-border);
	}
</style>
