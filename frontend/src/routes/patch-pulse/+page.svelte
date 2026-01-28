<script lang="ts">
	import api from '$lib/api';
	import type { PatchPulseResponse } from '$lib/types';
	import PatchBadge from '$lib/components/PatchBadge.svelte';
	import TopicCard from '$lib/components/TopicCard.svelte';
	import SentimentBar from '$lib/components/SentimentBar.svelte';
	import QuoteCard from '$lib/components/QuoteCard.svelte';
	import FollowButton from '$lib/components/FollowButton.svelte';

	let data: PatchPulseResponse | null = $state(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function loadPatchPulse() {
		loading = true;
		error = null;
		try {
			data = await api.getPatchPulse({ limit: 10 });
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load patch pulse';
			console.error('Failed to load patch pulse:', e);
		} finally {
			loading = false;
		}
	}

	// Load on mount
	$effect(() => {
		loadPatchPulse();
	});

	// Get top 3 quotes across all topics
	const topQuotes = $derived(() => {
		if (!data?.topics) return [];
		return data.topics
			.flatMap((t) => t.quotes || [])
			.sort((a, b) => b.confidence - a.confidence)
			.slice(0, 3);
	});
</script>

<svelte:head>
	<title>Patch Pulse - CommunityPulse</title>
	<meta name="description" content="Community sentiment for the current gaming patch" />
</svelte:head>

<div class="patch-pulse-page">
	<header class="page-header">
		<h1>Patch Pulse</h1>
		<p class="subtitle">What the community is saying about the current patch</p>
	</header>

	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading patch data...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button onclick={loadPatchPulse} class="btn btn-primary">Try Again</button>
		</div>
	{:else if data}
		<div class="pulse-content">
			<!-- Patch Info -->
			<section class="patch-info">
				<PatchBadge patch={data.patch} lastUpdated={data.last_updated} />
				<div class="stats">
					<span class="stat">
						<strong>{data.topics.length}</strong> topics
					</span>
					<span class="stat">
						<strong>{data.total_posts}</strong> posts analyzed
					</span>
				</div>
			</section>

			<!-- Overall Sentiment -->
			<section class="overall-sentiment">
				<h2>Overall Sentiment</h2>
				<div class="sentiment-display">
					<SentimentBar
						sentiment={{
							positive: data.overall_sentiment.positive,
							neutral: data.overall_sentiment.neutral,
							negative: data.overall_sentiment.negative
						}}
					/>
					<div class="sentiment-labels">
						<span class="positive">{data.overall_sentiment.positive.toFixed(1)}% Positive</span>
						<span class="neutral">{data.overall_sentiment.neutral.toFixed(1)}% Neutral</span>
						<span class="negative">{data.overall_sentiment.negative.toFixed(1)}% Negative</span>
					</div>
				</div>
			</section>

			<!-- Top Topics -->
			<section class="top-topics">
				<h2>Hot Topics This Patch</h2>
				<div class="topics-grid">
					{#each data.topics as topic (topic.slug)}
						<div class="topic-card-wrapper">
							<TopicCard {topic} />
							<div class="topic-follow-action">
								<FollowButton slug={topic.slug} name={topic.name} compact />
							</div>
						</div>
					{/each}
				</div>
				{#if data.topics.length === 0}
					<p class="empty-state">No topics yet for this patch. Check back soon!</p>
				{/if}
			</section>

			<!-- Top Quotes -->
			{#if topQuotes().length > 0}
				<section class="top-quotes">
					<h2>What Players Are Saying</h2>
					<div class="quotes-list">
						{#each topQuotes() as quote}
							<QuoteCard {quote} />
						{/each}
					</div>
				</section>
			{/if}
		</div>
	{/if}
</div>

<style>
	.patch-pulse-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: var(--spacing-lg);
	}

	.page-header {
		margin-bottom: var(--spacing-xl);
	}

	.page-header h1 {
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-bold);
		margin-bottom: var(--spacing-xs);
	}

	.subtitle {
		color: var(--color-text-secondary);
	}

	.loading-state,
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-2xl);
		text-align: center;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-border);
		border-top-color: var(--color-accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: var(--spacing-md);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.error-message {
		color: var(--color-negative);
		margin-bottom: var(--spacing-md);
	}

	.btn {
		padding: var(--spacing-sm) var(--spacing-lg);
		border-radius: var(--radius-md);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		border: none;
	}

	.btn-primary {
		background: var(--color-accent);
		color: white;
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	.pulse-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xl);
	}

	.patch-info {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: var(--spacing-md);
	}

	.stats {
		display: flex;
		gap: var(--spacing-lg);
	}

	.stat {
		color: var(--color-text-secondary);
	}

	.stat strong {
		color: var(--color-text-primary);
	}

	section h2 {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		margin-bottom: var(--spacing-md);
	}

	.overall-sentiment {
		background: var(--color-surface);
		padding: var(--spacing-lg);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-border);
	}

	.sentiment-display {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.sentiment-labels {
		display: flex;
		justify-content: space-between;
		font-size: var(--font-size-sm);
	}

	.sentiment-labels .positive {
		color: var(--color-positive);
	}
	.sentiment-labels .neutral {
		color: var(--color-text-secondary);
	}
	.sentiment-labels .negative {
		color: var(--color-negative);
	}

	.topics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--spacing-md);
	}

	.topic-card-wrapper {
		position: relative;
	}

	.topic-follow-action {
		position: absolute;
		top: var(--spacing-sm);
		right: var(--spacing-sm);
		z-index: 1;
	}

	.empty-state {
		color: var(--color-text-tertiary);
		text-align: center;
		padding: var(--spacing-xl);
	}

	.quotes-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	@media (max-width: 768px) {
		.patch-info {
			flex-direction: column;
			align-items: flex-start;
		}

		.stats {
			flex-direction: column;
			gap: var(--spacing-xs);
		}

		.sentiment-labels {
			flex-direction: column;
			gap: var(--spacing-xs);
		}
	}
</style>
