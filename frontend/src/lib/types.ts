/** Platform sources for content */
export type Platform = 'youtube' | 'official-news' | 'tier-site' | 'guide-site' | 'google_trends';

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

/** Sentiment factor explaining why sentiment is positive/negative */
export interface SentimentFactor {
	type: string;
	description: string;
	impact: 'positive' | 'negative' | 'neutral';
}

/** Sentiment explanation data */
export interface SentimentExplanation {
	dominant_sentiment: SentimentLabel;
	strength: 'strong' | 'moderate' | 'mixed';
	primary_reason: string;
	factors: SentimentFactor[];
	sentiment_distribution_note: string;
}

/** Confidence contributing factor */
export interface ConfidenceFactor {
	name: string;
	score: number;
	weight: number;
	explanation: string;
}

/** Confidence breakdown data */
export interface ConfidenceBreakdown {
	overall_score: number;
	level: 'high' | 'medium' | 'low';
	factors: ConfidenceFactor[];
	limitations: string[] | null;
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
	sentiment_explanation: SentimentExplanation | null;
	confidence_breakdown: ConfidenceBreakdown | null;
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
	last_updated: string | null;
	filters: {
		themes: string[] | null;
		platforms: string[] | null;
		period_days: number;
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

/** Vote type for feedback */
export type VoteType = 'thumbs_up' | 'thumbs_down';

/** Report reason */
export type ReportReason = 'misleading' | 'inaccurate_quotes' | 'wrong_sentiment' | 'other';

/** Vote request */
export interface VoteRequest {
	topic_slug: string;
	vote_type: VoteType;
	session_id: string;
}

/** Report request */
export interface ReportRequest {
	topic_slug: string;
	reason: ReportReason;
	details?: string;
	session_id: string;
}

/** General feedback request */
export interface GeneralFeedbackRequest {
	message: string;
	email?: string;
	session_id: string;
}

/** Feedback response */
export interface FeedbackResponse {
	success: boolean;
	message: string;
}

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
