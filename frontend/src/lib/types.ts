/** Platform sources for content */
export type Platform = 'youtube' | 'official-news' | 'tier-site' | 'guide-site' | 'reddit' | 'google_trends';

/** Sentiment label values */
export type SentimentLabel = 'positive' | 'neutral' | 'negative';

/** Sentiment distribution breakdown */
export interface Sentiment {
	positive: number;
	neutral: number;
	negative: number;
}

/** Representative quote from a topic */
export interface Quote {
	text: string;
	source_url: string;
	platform: Platform;
	sentiment: SentimentLabel;
	confidence: number;
}

/** Time period for aggregation */
export interface Period {
	start: string | null;
	end: string | null;
}

/** Topic aggregation data */
export interface Topic {
	slug: string;
	name: string;
	sentiment: Sentiment;
	post_count: number;
	source_mix: Record<string, number>;
	quotes: Quote[];
	confidence: number | null;
	period: Period;
	summary: string | null;
}

/** Minimal topic info for navigation */
export interface TopicNavItem {
	slug: string;
	name: string;
	post_count: number;
}

/** Trending topics response */
export interface TrendingResponse {
	topics: Topic[];
	count: number;
	filters: {
		themes: string[] | null;
		limit: number;
	};
}

/** Topics list response */
export interface TopicsListResponse {
	topics: TopicNavItem[];
	count: number;
}

/** Sources distribution response */
export interface SourcesResponse {
	sources: Record<string, number>;
	percentages: Record<string, number>;
	total: number;
}

/** Aggregation trigger response */
export interface AggregateResponse {
	status: string;
	topics_aggregated: number;
	config: {
		period_days: number;
		min_posts: number;
	};
}

/** Active filters state */
export interface FilterState {
	themes: string[];
	platforms: Platform[];
	dateRange: '7d' | '14d' | '30d';
}

/** Theme preference */
export type ThemeMode = 'dark' | 'light' | 'system';

/** Overall sentiment across all topics */
export interface OverallSentiment {
	positive: number;
	neutral: number;
	negative: number;
}

/** Patch Pulse response */
export interface PatchPulseResponse {
	patch: string;
	topics: Topic[];
	overall_sentiment: OverallSentiment;
	total_posts: number;
	last_updated: string;
}
