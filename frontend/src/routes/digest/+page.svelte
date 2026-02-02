<script lang="ts">
	import { trackedTopics, type TrackedTopic } from '$lib/stores/tracking.svelte';
	import api, { type DigestSummaryResponse } from '$lib/api';
	import type { Topic } from '$lib/types';
	import DigestCard from '$lib/components/DigestCard.svelte';

	let topicsData: Topic[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// AI Summary state
	let showAiSummary = $state(false);
	let aiSummary = $state<DigestSummaryResponse | null>(null);
	let aiSummaryLoading = $state(false);
	let aiSummaryError = $state<string | null>(null);

	// Load full topic data for tracked slugs
	async function loadDigestTopics() {
		const tracked = trackedTopics.current;

		if (tracked.length === 0) {
			topicsData = [];
			loading = false;
			return;
		}

		loading = true;
		error = null;

		try {
			const promises = tracked.map((t: TrackedTopic) => api.getTopic(t.slug));
			const results = await Promise.allSettled(promises);

			topicsData = results
				.filter((r): r is PromiseFulfilledResult<Topic> => r.status === 'fulfilled')
				.map((r: PromiseFulfilledResult<Topic>) => r.value);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load topics';
			console.error('Failed to load digest topics:', e);
		} finally {
			loading = false;
		}
	}

	// Load AI summary when toggled on
	async function loadAiSummary() {
		const tracked = trackedTopics.current;
		if (tracked.length === 0) return;

		aiSummaryLoading = true;
		aiSummaryError = null;

		try {
			const slugs = tracked.map((t: TrackedTopic) => t.slug);
			aiSummary = await api.getDigestSummary(slugs);
		} catch (e) {
			aiSummaryError = e instanceof Error ? e.message : 'Failed to generate summary';
			console.error('Failed to load AI summary:', e);
		} finally {
			aiSummaryLoading = false;
		}
	}

	// Toggle AI summary
	function toggleAiSummary() {
		showAiSummary = !showAiSummary;
		if (showAiSummary && !aiSummary && !aiSummaryLoading) {
			loadAiSummary();
		}
	}

	// Re-fetch when tracked topics change
	$effect(() => {
		trackedTopics.current; // Subscribe to store changes
		loadDigestTopics();
		// Reset AI summary when topics change
		aiSummary = null;
	});

	// Sort by most recently updated (period.end)
	const sortedTopics = $derived(
		[...topicsData].sort((a: Topic, b: Topic) => {
			const aEnd = a.period.end ? new Date(a.period.end).getTime() : 0;
			const bEnd = b.period.end ? new Date(b.period.end).getTime() : 0;
			return bEnd - aEnd;
		})
	);

	// Count topics updated in last 24 hours
	const newTodayCount = $derived(() => {
		const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
		return sortedTopics.filter((t: Topic) => {
			if (!t.period.end) return false;
			return new Date(t.period.end) > oneDayAgo;
		}).length;
	});
</script>

<svelte:head>
	<title>Your Daily Digest - CommunityPulse</title>
	<meta name="description" content="Daily digest of your followed topics" />
</svelte:head>

<div class="digest-page">
	<header class="page-header">
		<div class="header-top">
			<div>
				<h1>Your Daily Digest</h1>
				<p class="subtitle">
					{#if trackedTopics.current.length > 0}
						{trackedTopics.current.length} topic{trackedTopics.current.length === 1 ? '' : 's'} followed
						{#if newTodayCount() > 0}
							<span class="new-highlight">• {newTodayCount()} updated today</span>
						{/if}
					{:else}
						Follow topics to see your personalized digest
					{/if}
				</p>
			</div>
			{#if trackedTopics.current.length > 0}
				<button
					class="ai-toggle"
					class:active={showAiSummary}
					onclick={toggleAiSummary}
					disabled={aiSummaryLoading}
				>
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M12 2L2 7l10 5 10-5-10-5z" />
						<path d="M2 17l10 5 10-5" />
						<path d="M2 12l10 5 10-5" />
					</svg>
					{showAiSummary ? 'Hide AI Summary' : 'AI Summary'}
				</button>
			{/if}
		</div>
	</header>

	{#if showAiSummary && trackedTopics.current.length > 0}
		<div class="ai-summary-section">
			{#if aiSummaryLoading}
				<div class="ai-summary-loading">
					<div class="spinner-small"></div>
					<span>Generating your personalized summary...</span>
				</div>
			{:else if aiSummaryError}
				<div class="ai-summary-error">
					<p>{aiSummaryError}</p>
					<button onclick={loadAiSummary} class="btn btn-secondary">Try Again</button>
				</div>
			{:else if aiSummary}
				<div class="ai-summary-content">
					<div class="ai-summary-header">
						<span class="ai-badge">
							{aiSummary.is_ai_generated ? 'AI Generated' : 'Auto Summary'}
						</span>
						<span class="ai-meta">
							{aiSummary.topic_count} topic{aiSummary.topic_count === 1 ? '' : 's'}
						</span>
					</div>
					<p class="ai-summary-text">{aiSummary.summary}</p>
				</div>
			{/if}
		</div>
	{/if}

	{#if loading && trackedTopics.current.length > 0}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading your digest...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button onclick={loadDigestTopics} class="btn btn-primary">Try Again</button>
		</div>
	{:else if trackedTopics.current.length === 0}
		<div class="empty-state">
			<div class="empty-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<rect x="3" y="4" width="18" height="18" rx="2" />
					<line x1="16" y1="2" x2="16" y2="6" />
					<line x1="8" y1="2" x2="8" y2="6" />
					<line x1="3" y1="10" x2="21" y2="10" />
				</svg>
			</div>
			<h2>No topics in your digest</h2>
			<p>Follow topics from the dashboard or trending list to see personalized summaries here.</p>
			<a href="/" class="btn btn-primary">Browse Topics</a>
		</div>
	{:else}
		<div class="digest-grid">
			{#each sortedTopics as topic (topic.slug)}
				<DigestCard {topic} />
			{/each}
		</div>
	{/if}
</div>

<style>
	.digest-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: var(--spacing-lg);
	}

	.page-header {
		margin-bottom: var(--spacing-xl);
	}

	.header-top {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: var(--spacing-md);
		flex-wrap: wrap;
	}

	.page-header h1 {
		font-size: var(--font-size-2xl);
		font-weight: var(--font-weight-bold);
		margin-bottom: var(--spacing-xs);
	}

	.subtitle {
		color: var(--color-text-secondary);
	}

	.new-highlight {
		color: var(--color-accent);
		font-weight: var(--font-weight-medium);
	}

	.ai-toggle {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		color: var(--color-text-secondary);
		font-size: var(--font-size-sm);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.ai-toggle:hover {
		background: var(--color-bg-card-hover);
		border-color: var(--color-border-hover);
	}

	.ai-toggle.active {
		background: var(--color-accent);
		border-color: var(--color-accent);
		color: white;
	}

	.ai-toggle:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.ai-toggle svg {
		width: 16px;
		height: 16px;
	}

	.ai-summary-section {
		background: var(--color-bg-card);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: var(--spacing-lg);
		margin-bottom: var(--spacing-xl);
	}

	.ai-summary-loading {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		color: var(--color-text-secondary);
	}

	.spinner-small {
		width: 20px;
		height: 20px;
		border: 2px solid var(--color-border);
		border-top-color: var(--color-accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.ai-summary-error {
		text-align: center;
		color: var(--color-negative);
	}

	.ai-summary-error p {
		margin-bottom: var(--spacing-sm);
	}

	.ai-summary-content {
		/* Content styling */
	}

	.ai-summary-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}

	.ai-badge {
		display: inline-flex;
		align-items: center;
		padding: 2px 8px;
		background: linear-gradient(135deg, var(--color-accent), #9333ea);
		color: white;
		font-size: var(--font-size-xs);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-full);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.ai-meta {
		font-size: var(--font-size-xs);
		color: var(--color-text-muted);
	}

	.ai-summary-text {
		font-size: var(--font-size-md);
		line-height: 1.7;
		color: var(--color-text-primary);
	}

	.btn-secondary {
		background: var(--color-bg-secondary);
		color: var(--color-text-primary);
		border: 1px solid var(--color-border);
	}

	.btn-secondary:hover {
		background: var(--color-bg-card-hover);
	}

	.loading-state,
	.error-state,
	.empty-state {
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

	.empty-icon {
		width: 64px;
		height: 64px;
		color: var(--color-text-tertiary);
		margin-bottom: var(--spacing-md);
	}

	.empty-icon svg {
		width: 100%;
		height: 100%;
	}

	.empty-state h2 {
		font-size: var(--font-size-lg);
		margin-bottom: var(--spacing-sm);
	}

	.empty-state p {
		color: var(--color-text-secondary);
		margin-bottom: var(--spacing-lg);
		max-width: 400px;
	}

	.btn {
		padding: var(--spacing-sm) var(--spacing-lg);
		border-radius: var(--radius-md);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		border: none;
		text-decoration: none;
		display: inline-block;
	}

	.btn-primary {
		background: var(--color-accent);
		color: white;
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	.digest-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: var(--spacing-md);
	}
</style>
