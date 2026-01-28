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
	FeedbackResponse
} from './types';

const API_BASE = 'http://localhost:8000/api';

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
	 * Get trending topics with optional theme filter
	 */
	async getTrending(options?: { themes?: string[]; limit?: number }): Promise<TrendingResponse> {
		const endpoint = buildUrl('/dashboard/trending', {
			theme: options?.themes,
			limit: options?.limit
		});
		return fetchApi<TrendingResponse>(endpoint);
	},

	/**
	 * Get all topics for navigation sidebar
	 */
	async getTopics(): Promise<TopicsListResponse> {
		return fetchApi<TopicsListResponse>('/dashboard/topics');
	},

	/**
	 * Get a single topic by slug
	 */
	async getTopic(slug: string): Promise<Topic> {
		return fetchApi<Topic>(`/dashboard/topics/${encodeURIComponent(slug)}`);
	},

	/**
	 * Get source distribution
	 */
	async getSources(): Promise<SourcesResponse> {
		return fetchApi<SourcesResponse>('/dashboard/sources');
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
		return fetchApi<PatchPulseResponse>(endpoint);
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
	}
};

export default api;
