/**
 * API client for CommunityPulse dashboard
 */

import type {
	TrendingResponse,
	TopicsListResponse,
	Topic,
	SourcesResponse,
	AggregateResponse,
	PatchPulseResponse,
	VoteRequest,
	ReportRequest,
	GeneralFeedbackRequest,
	FeedbackResponse
} from './types';

const API_BASE = 'http://localhost:8000/api';

/** Simple in-memory cache for GET requests */
interface CacheEntry<T> {
	data: T;
	timestamp: number;
}

const cache = new Map<string, CacheEntry<unknown>>();
const DEFAULT_CACHE_TTL = 30 * 1000; // 30 seconds

function getCached<T>(key: string, ttl: number = DEFAULT_CACHE_TTL): T | null {
	const entry = cache.get(key);
	if (!entry) return null;
	if (Date.now() - entry.timestamp > ttl) {
		cache.delete(key);
		return null;
	}
	return entry.data as T;
}

function setCache<T>(key: string, data: T): void {
	cache.set(key, { data, timestamp: Date.now() });
}

/** Clear all cached data */
export function clearCache(): void {
	cache.clear();
}

/** Generic fetch wrapper with error handling */
async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const url = `${API_BASE}${endpoint}`;

	const response = await fetch(url, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options.headers
		}
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
		throw new Error(error.detail || `HTTP ${response.status}`);
	}

	return response.json();
}

/** Build URL with query parameters */
function buildUrl(endpoint: string, params: Record<string, string | string[] | number | undefined>): string {
	const searchParams = new URLSearchParams();

	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null) continue;

		if (Array.isArray(value)) {
			for (const v of value) {
				searchParams.append(key, v);
			}
		} else {
			searchParams.append(key, String(value));
		}
	}

	const queryString = searchParams.toString();
	return queryString ? `${endpoint}?${queryString}` : endpoint;
}

/**
 * Dashboard API client
 */
export const api = {
	/**
	 * Get trending topics with optional theme and platform filters
	 */
	async getTrending(options?: { themes?: string[]; platforms?: string[]; limit?: number }): Promise<TrendingResponse> {
		const endpoint = buildUrl('/dashboard/trending', {
			theme: options?.themes,
			platform: options?.platforms,
			limit: options?.limit
		});
		const cacheKey = `trending:${endpoint}`;
		const cached = getCached<TrendingResponse>(cacheKey);
		if (cached) return cached;

		const data = await fetchApi<TrendingResponse>(endpoint);
		setCache(cacheKey, data);
		return data;
	},

	/**
	 * Get all topics for navigation sidebar
	 */
	async getTopics(): Promise<TopicsListResponse> {
		const cacheKey = 'topics:list';
		const cached = getCached<TopicsListResponse>(cacheKey);
		if (cached) return cached;

		const data = await fetchApi<TopicsListResponse>('/dashboard/topics');
		setCache(cacheKey, data);
		return data;
	},

	/**
	 * Get a single topic by slug
	 */
	async getTopic(slug: string): Promise<Topic> {
		const cacheKey = `topic:${slug}`;
		const cached = getCached<Topic>(cacheKey);
		if (cached) return cached;

		const data = await fetchApi<Topic>(`/dashboard/topics/${encodeURIComponent(slug)}`);
		setCache(cacheKey, data);
		return data;
	},

	/**
	 * Get source distribution
	 */
	async getSources(): Promise<SourcesResponse> {
		const cacheKey = 'sources';
		const cached = getCached<SourcesResponse>(cacheKey);
		if (cached) return cached;

		const data = await fetchApi<SourcesResponse>('/dashboard/sources');
		setCache(cacheKey, data);
		return data;
	},

	/**
	 * Trigger manual aggregation
	 */
	async triggerAggregation(options?: {
		periodDays?: number;
		minPosts?: number;
	}): Promise<AggregateResponse> {
		const endpoint = buildUrl('/dashboard/aggregate', {
			period_days: options?.periodDays,
			min_posts: options?.minPosts
		});
		return fetchApi<AggregateResponse>(endpoint, { method: 'POST' });
	},

	/**
	 * Get Patch Pulse data for current patch
	 */
	async getPatchPulse(options?: { limit?: number }): Promise<PatchPulseResponse> {
		const endpoint = buildUrl('/dashboard/patch-pulse', {
			limit: options?.limit
		});
		const cacheKey = `patchpulse:${endpoint}`;
		const cached = getCached<PatchPulseResponse>(cacheKey);
		if (cached) return cached;

		const data = await fetchApi<PatchPulseResponse>(endpoint);
		setCache(cacheKey, data);
		return data;
	},

	/**
	 * Submit a vote (thumbs up/down) on a topic summary
	 */
	async submitVote(request: VoteRequest): Promise<FeedbackResponse> {
		return fetchApi<FeedbackResponse>('/feedback/vote', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	},

	/**
	 * Submit a report for a topic summary
	 */
	async submitReport(request: ReportRequest): Promise<FeedbackResponse> {
		return fetchApi<FeedbackResponse>('/feedback/report', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	},

	/**
	 * Submit general feedback about the application
	 */
	async submitGeneralFeedback(request: GeneralFeedbackRequest): Promise<FeedbackResponse> {
		return fetchApi<FeedbackResponse>('/feedback/general', {
			method: 'POST',
			body: JSON.stringify(request)
		});
	},

	/**
	 * Generate AI-powered digest summary for followed topics
	 */
	async getDigestSummary(slugs: string[]): Promise<DigestSummaryResponse> {
		return fetchApi<DigestSummaryResponse>('/dashboard/digest/summary', {
			method: 'POST',
			body: JSON.stringify(slugs)
		});
	}
};

/** Response from digest summary endpoint */
export interface DigestSummaryResponse {
	summary: string;
	generated_at: string;
	topic_count: number;
	is_ai_generated: boolean;
}

export default api;
