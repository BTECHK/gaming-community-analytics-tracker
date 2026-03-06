<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import api from '$lib/api';
	import type {
		Topic, TopicNavItem, FilterState, Quote, StatsResponse,
		SentimentHistoryEntry, ActivityResponse
	} from '$lib/types';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import FreshnessIndicator from '$lib/components/FreshnessIndicator.svelte';
	import TopicCard from '$lib/components/TopicCard.svelte';
	import MentionsFeed from '$lib/components/MentionsFeed.svelte';
	import TopicCloud from '$lib/components/TopicCloud.svelte';
	import StatsBanner from '$lib/components/StatsBanner.svelte';
	import SentimentDonut from '$lib/components/SentimentDonut.svelte';
	import MentionsTimeline from '$lib/components/MentionsTimeline.svelte';
	import ActivityHeatmap from '$lib/components/ActivityHeatmap.svelte';
	import PlatformBreakdown from '$lib/components/PlatformBreakdown.svelte';
	import FollowButton from '$lib/components/FollowButton.svelte';
	import LazyLoad from '$lib/components/LazyLoad.svelte';

	// State
	let topics: Topic[] = $state([]);
	let allTopics: TopicNavItem[] = $state([]);
	let sources: Record<string, number> = $state({});
	let sourcePercentages: Record<string, number> = $state({});
	let stats: StatsResponse | null = $state(null);
	let sentimentHistory: SentimentHistoryEntry[] = $state([]);
	let activityData: ActivityResponse | null = $state(null);
	let lastUpdated = $state<string | null>(null);
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

	// Overall sentiment from history data
	const overallSentiment = $derived(() => {
		if (sentimentHistory.length === 0) return { positive: 0, neutral: 0, negative: 0 };
		const total = sentimentHistory.length;
		return {
			positive: sentimentHistory.reduce((s, h) => s + h.positive, 0) / total,
			neutral: sentimentHistory.reduce((s, h) => s + h.neutral, 0) / total,
			negative: sentimentHistory.reduce((s, h) => s + h.negative, 0) / total,
		};
	});

	// Parse URL parameters on mount and when URL changes
	function parseUrlFilters() {
		const url = $page.url;
		const themeParam = url.searchParams.getAll('theme');
		const platformParam = url.searchParams.getAll('platform') as FilterState['platforms'];
		const dateRangeParam = url.searchParams.get('dateRange') as FilterState['dateRange'] | null;
		filters = {
			themes: themeParam,
			platforms: platformParam,
			dateRange: dateRangeParam || '7d'
		};
	}

	// Update URL when filters change
	function updateUrl(newFilters: FilterState) {
		const url = new URL(window.location.href);
		url.searchParams.delete('theme');
		url.searchParams.delete('platform');
		url.searchParams.delete('dateRange');
		for (const theme of newFilters.themes) {
			url.searchParams.append('theme', theme);
		}
		for (const platform of newFilters.platforms) {
			url.searchParams.append('platform', platform);
		}
		if (newFilters.dateRange !== '7d') {
			url.searchParams.set('dateRange', newFilters.dateRange);
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
			const [trendingRes, topicsRes, sourcesRes, statsRes, historyRes, activityRes] = await Promise.all([
				api.getTrending({
					themes: filters.themes.length > 0 ? filters.themes : undefined,
					platforms: filters.platforms.length > 0 ? filters.platforms : undefined,
					periodDays: parseInt(filters.dateRange)
				}),
				api.getTopics(),
				api.getSources(),
				api.getStats(),
				api.getSentimentHistory(),
				api.getActivity()
			]);

			topics = trendingRes.topics;
			lastUpdated = trendingRes.last_updated;
			allTopics = topicsRes.topics;
			sources = sourcesRes.sources;
			sourcePercentages = sourcesRes.percentages;
			stats = statsRes;
			sentimentHistory = historyRes.history;
			activityData = activityRes;
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
	<!-- Row 1: Stats Banner -->
	{#if stats}
		<StatsBanner {stats} />
	{/if}

	<FilterBar {filters} onFiltersChange={handleFiltersChange} />
	<FreshnessIndicator {lastUpdated} />

	{#if loading}
		<div class="loading-state">
			<div class="loading-grid">
				{#each Array(6) as _}
					<div class="skeleton-card skeleton"></div>
				{/each}
			</div>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button class="btn btn-primary" onclick={loadData}>Retry</button>
		</div>
	{:else}
		<!-- Row 2: Sentiment Donut + Activity Timeline -->
		<div class="tile-row row-2">
			<div class="tile-1col">
				<SentimentDonut
					positive={overallSentiment().positive}
					neutral={overallSentiment().neutral}
					negative={overallSentiment().negative}
				/>
			</div>
			<div class="tile-2col">
				<MentionsTimeline data={sentimentHistory} />
			</div>
		</div>

		<!-- Row 3: Trending Topics + Mentions Feed -->
		<div class="tile-row row-3">
			<div class="tile-2col">
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
			</div>
			<div class="tile-1col">
				<MentionsFeed quotes={allQuotes} />
			</div>
		</div>

		<!-- Row 4: Activity Heatmap + Platform Breakdown -->
		<div class="tile-row row-4">
			<div class="tile-2col">
				<LazyLoad minHeight="200px">
					{#if activityData}
						<ActivityHeatmap heatmap={activityData.heatmap} />
					{/if}
				</LazyLoad>
			</div>
			<div class="tile-1col">
				<PlatformBreakdown {sources} percentages={sourcePercentages} />
			</div>
		</div>

		<!-- Row 5: Topic Cloud -->
		<div class="tile-row row-5">
			<div class="tile-full">
				<LazyLoad minHeight="150px">
					<TopicCloud topics={allTopics} />
				</LazyLoad>
			</div>
		</div>
	{/if}
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-lg);
	}

	/* Tile rows: 3-column grid */
	.tile-row {
		display: grid;
		grid-template-columns: 1fr 2fr;
		gap: var(--spacing-lg);
	}

	.tile-row.row-3,
	.tile-row.row-4 {
		grid-template-columns: 2fr 1fr;
	}

	.tile-row.row-5 {
		grid-template-columns: 1fr;
	}

	.tile-1col,
	.tile-2col,
	.tile-full {
		min-width: 0;
	}

	/* Responsive: collapse to single column */
	@media (max-width: 1200px) {
		.tile-row {
			grid-template-columns: 1fr 1fr;
		}
		.tile-row.row-3,
		.tile-row.row-4 {
			grid-template-columns: 1fr 1fr;
		}
	}

	@media (max-width: 768px) {
		.tile-row,
		.tile-row.row-3,
		.tile-row.row-4 {
			grid-template-columns: 1fr;
		}
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
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: var(--spacing-lg);
	}

	.skeleton-card {
		height: 200px;
		border-radius: var(--radius-lg);
		background: rgba(18, 18, 26, 0.8);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid var(--color-border);
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
