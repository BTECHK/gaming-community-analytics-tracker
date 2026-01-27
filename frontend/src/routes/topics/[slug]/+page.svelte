<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import api from '$lib/api';
	import type { Topic } from '$lib/types';
	import SentimentBar from '$lib/components/SentimentBar.svelte';
	import ConfidenceIndicator from '$lib/components/ConfidenceIndicator.svelte';
	import QuoteCard from '$lib/components/QuoteCard.svelte';
	import SourcesCard from '$lib/components/SourcesCard.svelte';

	let topic: Topic | null = $state(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	const slug = $derived($page.params.slug);

	// Calculate source percentages from topic's source_mix
	const sourcePercentages = $derived(() => {
		if (!topic || !topic.source_mix) return {};
		const total = Object.values(topic.source_mix).reduce((a, b) => a + b, 0);
		if (total === 0) return {};
		return Object.fromEntries(
			Object.entries(topic.source_mix).map(([k, v]) => [k, (v / total) * 100])
		);
	});

	async function loadTopic() {
		loading = true;
		error = null;

		try {
			topic = await api.getTopic(slug);
		} catch (e) {
			console.error('Failed to load topic:', e);
			error = e instanceof Error ? e.message : 'Failed to load topic';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadTopic();
	});

	// Reload when slug changes
	$effect(() => {
		if (slug) {
			loadTopic();
		}
	});
</script>

<svelte:head>
	{#if topic}
		<title>{topic.name} - CommunityPulse</title>
		<meta name="description" content="Community sentiment analysis for {topic.name}" />
	{:else}
		<title>Topic - CommunityPulse</title>
	{/if}
</svelte:head>

<div class="topic-page">
	<!-- Back navigation -->
	<nav class="breadcrumb">
		<a href="/" class="back-link">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<polyline points="15 18 9 12 15 6" />
			</svg>
			Back to Trending
		</a>
	</nav>

	{#if loading}
		<div class="loading-state">
			<div class="skeleton skeleton-header"></div>
			<div class="skeleton skeleton-bar"></div>
			<div class="skeleton skeleton-content"></div>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button class="btn btn-primary" onclick={loadTopic}>
				Retry
			</button>
		</div>
	{:else if topic}
		<div class="topic-content">
			<!-- Header -->
			<header class="topic-header">
				<h1 class="topic-name">{topic.name}</h1>
				{#if topic.summary}
					<p class="topic-summary">{topic.summary}</p>
				{/if}
			</header>

			<!-- Sentiment section -->
			<section class="section sentiment-section">
				<h2 class="section-title">Sentiment Breakdown</h2>
				<div class="sentiment-card card">
					<SentimentBar sentiment={topic.sentiment} height={40} />
					<div class="sentiment-details">
						<div class="sentiment-stat positive">
							<span class="stat-value">{topic.sentiment.positive.toFixed(1)}%</span>
							<span class="stat-label">Positive</span>
						</div>
						<div class="sentiment-stat neutral">
							<span class="stat-value">{topic.sentiment.neutral.toFixed(1)}%</span>
							<span class="stat-label">Neutral</span>
						</div>
						<div class="sentiment-stat negative">
							<span class="stat-value">{topic.sentiment.negative.toFixed(1)}%</span>
							<span class="stat-label">Negative</span>
						</div>
					</div>
				</div>
			</section>

			<!-- Stats section -->
			<section class="section stats-section">
				<div class="stats-grid">
					<div class="stat-card card">
						<span class="stat-icon">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
							</svg>
						</span>
						<span class="stat-value">{topic.post_count}</span>
						<span class="stat-label">Posts</span>
					</div>
					<div class="stat-card card">
						<span class="stat-icon">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
								<line x1="8" y1="21" x2="16" y2="21" />
								<line x1="12" y1="17" x2="12" y2="21" />
							</svg>
						</span>
						<span class="stat-value">{Object.keys(topic.source_mix || {}).length}</span>
						<span class="stat-label">Sources</span>
					</div>
					<div class="stat-card card">
						<span class="stat-icon">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<circle cx="12" cy="12" r="10" />
								<polyline points="12 6 12 12 16 14" />
							</svg>
						</span>
						<ConfidenceIndicator confidence={topic.confidence} />
					</div>
				</div>
			</section>

			<!-- Main grid -->
			<div class="main-grid">
				<!-- Quotes section -->
				<section class="section quotes-section">
					<h2 class="section-title">What People Are Saying</h2>
					{#if topic.quotes && topic.quotes.length > 0}
						<div class="quotes-list">
							{#each topic.quotes as quote (quote.source_url)}
								<QuoteCard {quote} />
							{/each}
						</div>
					{:else}
						<div class="empty-state">
							<p>No quotes available</p>
						</div>
					{/if}
				</section>

				<!-- Sources breakdown -->
				<section class="section sources-section">
					<h2 class="section-title">Source Breakdown</h2>
					<SourcesCard sources={topic.source_mix || {}} percentages={sourcePercentages()} />
				</section>
			</div>
		</div>
	{/if}
</div>

<style>
	.topic-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xl);
	}

	.breadcrumb {
		margin-bottom: var(--spacing-md);
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-xs);
		color: var(--color-text-secondary);
		text-decoration: none;
		font-size: var(--font-size-sm);
		transition: color 0.2s ease;
	}

	.back-link:hover {
		color: var(--color-text-primary);
	}

	.back-link svg {
		width: 18px;
		height: 18px;
	}

	.topic-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xl);
	}

	.topic-header {
		margin-bottom: var(--spacing-lg);
	}

	.topic-name {
		font-size: var(--font-size-3xl);
		font-weight: var(--font-weight-bold);
		margin: 0 0 var(--spacing-sm) 0;
		text-transform: capitalize;
	}

	.topic-summary {
		font-size: var(--font-size-lg);
		color: var(--color-text-secondary);
		margin: 0;
		line-height: 1.6;
	}

	.section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.section-title {
		font-size: var(--font-size-lg);
		font-weight: var(--font-weight-semibold);
		margin: 0;
		color: var(--color-text-primary);
	}

	.sentiment-card {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-lg);
	}

	.sentiment-details {
		display: flex;
		justify-content: space-around;
		text-align: center;
	}

	.sentiment-stat {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.sentiment-stat .stat-value {
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-bold);
	}

	.sentiment-stat .stat-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.sentiment-stat.positive .stat-value {
		color: var(--color-positive);
	}

	.sentiment-stat.neutral .stat-value {
		color: var(--color-neutral);
	}

	.sentiment-stat.negative .stat-value {
		color: var(--color-negative);
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-md);
	}

	@media (max-width: 768px) {
		.stats-grid {
			grid-template-columns: 1fr;
		}
	}

	.stat-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		text-align: center;
	}

	.stat-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(139, 92, 246, 0.15);
		border-radius: var(--radius-md);
		color: var(--color-accent);
	}

	.stat-icon svg {
		width: 20px;
		height: 20px;
	}

	.stat-card .stat-value {
		font-size: var(--font-size-xl);
		font-weight: var(--font-weight-bold);
	}

	.stat-card .stat-label {
		font-size: var(--font-size-sm);
		color: var(--color-text-muted);
	}

	.main-grid {
		display: grid;
		grid-template-columns: 1fr 350px;
		gap: var(--spacing-xl);
	}

	@media (max-width: 1024px) {
		.main-grid {
			grid-template-columns: 1fr;
		}
	}

	.quotes-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-lg);
	}

	.skeleton-header {
		height: 60px;
		width: 60%;
	}

	.skeleton-bar {
		height: 40px;
	}

	.skeleton-content {
		height: 300px;
	}

	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-2xl);
		gap: var(--spacing-md);
	}

	.error-message {
		color: var(--color-negative);
		font-size: var(--font-size-lg);
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-2xl);
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		color: var(--color-text-muted);
	}
</style>
