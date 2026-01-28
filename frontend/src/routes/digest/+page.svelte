<script lang="ts">
	import { trackedTopics, type TrackedTopic } from '$lib/stores/tracking.svelte';
	import api from '$lib/api';
	import type { Topic } from '$lib/types';
	import DigestCard from '$lib/components/DigestCard.svelte';

	let topicsData: Topic[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

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

	// Re-fetch when tracked topics change
	$effect(() => {
		trackedTopics.current; // Subscribe to store changes
		loadDigestTopics();
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
	</header>

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
