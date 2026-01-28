<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import api from '$lib/api';
	import type { Topic, TopicNavItem, FilterState, Quote } from '$lib/types';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import TopicCard from '$lib/components/TopicCard.svelte';
	import MentionsFeed from '$lib/components/MentionsFeed.svelte';
	import TopicCloud from '$lib/components/TopicCloud.svelte';
	import SourcesCard from '$lib/components/SourcesCard.svelte';
	import FollowButton from '$lib/components/FollowButton.svelte';

	// State
	let topics: Topic[] = $state([]);
	let allTopics: TopicNavItem[] = $state([]);
	let sources: Record<string, number> = $state({});
	let sourcePercentages: Record<string, number> = $state({});
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Filters from URL
	let filters: FilterState = $state({
		themes: [],
		platforms: [],
		dateRange: '7d'
	});

	// Collect all quotes from topics for the mentions feed
	const allQuotes = $derived<Quote[]>(
		topics.flatMap((t) => t.quotes).slice(0, 20)
	);

	// Parse URL parameters on mount and when URL changes
	function parseUrlFilters() {
		const url = $page.url;
		const themeParam = url.searchParams.getAll('theme');
		filters = {
			themes: themeParam,
			platforms: [],
			dateRange: '7d'
		};
	}

	// Update URL when filters change
	function updateUrl(newFilters: FilterState) {
		const url = new URL(window.location.href);
		url.searchParams.delete('theme');
		for (const theme of newFilters.themes) {
			url.searchParams.append('theme', theme);
		}
		goto(url.pathname + url.search, { replaceState: true, noScroll: true });
	}

	function handleFiltersChange(newFilters: FilterState) {
		filters = newFilters;
		updateUrl(newFilters);
		loadData();
	}

	async function loadData() {
		loading = true;
		error = null;

		try {
			const [trendingRes, topicsRes, sourcesRes] = await Promise.all([
				api.getTrending({ themes: filters.themes.length > 0 ? filters.themes : undefined }),
				api.getTopics(),
				api.getSources()
			]);

			topics = trendingRes.topics;
			allTopics = topicsRes.topics;
			sources = sourcesRes.sources;
			sourcePercentages = sourcesRes.percentages;
		} catch (e) {
			console.error('Failed to load dashboard data:', e);
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		parseUrlFilters();
		loadData();
	});

	// React to URL changes
	$effect(() => {
		// This will re-run when $page.url changes
		$page.url;
		parseUrlFilters();
	});
</script>

<svelte:head>
	<title>Trending Now - CommunityPulse</title>
	<meta name="description" content="gaming community sentiment dashboard - see what players are talking about" />
</svelte:head>

<div class="dashboard">
	<FilterBar {filters} onFiltersChange={handleFiltersChange} />

	{#if loading}
		<div class="loading-state">
			<div class="loading-grid">
				{#each Array(4) as _, i}
					<div class="skeleton-card skeleton"></div>
				{/each}
			</div>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button class="btn btn-primary" onclick={loadData}>
				Retry
			</button>
		</div>
	{:else}
		<div class="dashboard-grid">
			<!-- Main content area -->
			<div class="main-column">
				<section class="section">
					<h2 class="section-title">Trending Topics</h2>
					{#if topics.length > 0}
						<div class="topic-grid">
							{#each topics as topic (topic.slug)}
								<div class="topic-card-wrapper">
									<TopicCard {topic} />
									<div class="topic-follow-action">
										<FollowButton slug={topic.slug} name={topic.name} compact />
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="empty-state">
							<p>No trending topics found</p>
							{#if filters.themes.length > 0}
								<p class="empty-hint">Try removing some filters</p>
							{/if}
						</div>
					{/if}
				</section>

				<section class="section">
					<TopicCloud topics={allTopics} />
				</section>
			</div>

			<!-- Sidebar content -->
			<div class="side-column">
				<MentionsFeed quotes={allQuotes} />
				<SourcesCard {sources} percentages={sourcePercentages} />
			</div>
		</div>
	{/if}
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xl);
	}

	.dashboard-grid {
		display: grid;
		grid-template-columns: 1fr 350px;
		gap: var(--spacing-xl);
	}

	@media (max-width: 1200px) {
		.dashboard-grid {
			grid-template-columns: 1fr;
		}

		.side-column {
			display: grid;
			grid-template-columns: 1fr 1fr;
			gap: var(--spacing-lg);
		}
	}

	@media (max-width: 768px) {
		.side-column {
			grid-template-columns: 1fr;
		}
	}

	.main-column {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xl);
	}

	.side-column {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xl);
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

	.topic-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--spacing-lg);
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

	.loading-state {
		padding: var(--spacing-xl);
	}

	.loading-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: var(--spacing-lg);
	}

	.skeleton-card {
		height: 200px;
		border-radius: var(--radius-lg);
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

	.empty-hint {
		font-size: var(--font-size-sm);
		opacity: 0.7;
	}
</style>
