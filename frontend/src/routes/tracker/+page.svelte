<script lang="ts">
	import { trackedTopics, type TrackedTopic } from '$lib/stores/tracking.svelte';
	import api from '$lib/api';
	import type { Topic } from '$lib/types';
	import TopicCard from '$lib/components/TopicCard.svelte';
	import FollowButton from '$lib/components/FollowButton.svelte';

	let topicsData: Topic[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Load full topic data for tracked slugs
	async function loadTrackedTopics() {
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

			// Check for any topics that no longer exist
			const existingSlugs = new Set(topicsData.map((t: Topic) => t.slug));
			const missingTopics = tracked.filter((t: TrackedTopic) => !existingSlugs.has(t.slug));
			if (missingTopics.length > 0) {
				console.warn('Some tracked topics no longer exist:', missingTopics);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load topics';
			console.error('Failed to load tracked topics:', e);
		} finally {
			loading = false;
		}
	}

	// Re-fetch when tracked topics change
	$effect(() => {
		trackedTopics.current; // Subscribe to store changes
		loadTrackedTopics();
	});

	// Sort by most recently followed
	const sortedTopics = $derived(
		[...topicsData].sort((a: Topic, b: Topic) => {
			const aTracked = trackedTopics.current.find((t: TrackedTopic) => t.slug === a.slug);
			const bTracked = trackedTopics.current.find((t: TrackedTopic) => t.slug === b.slug);
			if (!aTracked || !bTracked) return 0;
			return new Date(bTracked.followedAt).getTime() - new Date(aTracked.followedAt).getTime();
		})
	);
</script>

<svelte:head>
	<title>My Tracker - CommunityPulse</title>
	<meta name="description" content="Topics you're following on CommunityPulse" />
</svelte:head>

<div class="tracker-page">
	<header class="page-header">
		<h1>My Tracker</h1>
		<p class="subtitle">
			{#if trackedTopics.current.length > 0}
				Tracking {trackedTopics.current.length} topic{trackedTopics.current.length === 1
					? ''
					: 's'}
			{:else}
				Follow topics to track them here
			{/if}
		</p>
	</header>

	{#if loading && trackedTopics.current.length > 0}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading your topics...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button onclick={loadTrackedTopics} class="btn btn-primary">Try Again</button>
		</div>
	{:else if trackedTopics.current.length === 0}
		<div class="empty-state">
			<div class="empty-icon">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
					<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
				</svg>
			</div>
			<h2>No topics tracked yet</h2>
			<p>Browse trending topics and click the Follow button to track them here.</p>
			<a href="/" class="btn btn-primary">Browse Trending Topics</a>
		</div>
	{:else}
		<div class="tracked-topics">
			<div class="topics-list">
				{#each sortedTopics as topic (topic.slug)}
					<div class="tracked-topic-card">
						<TopicCard {topic} />
						<div class="card-actions">
							<FollowButton slug={topic.slug} name={topic.name} />
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.tracker-page {
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

	.topics-list {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--spacing-md);
	}

	.tracked-topic-card {
		position: relative;
	}

	.card-actions {
		position: absolute;
		top: var(--spacing-sm);
		right: var(--spacing-sm);
	}
</style>
