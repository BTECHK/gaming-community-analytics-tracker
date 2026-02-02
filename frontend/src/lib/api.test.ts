/**
 * Tests for API client.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, clearCache } from './api';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		clearCache();
	});

	afterEach(() => {
		clearCache();
	});

	describe('getTrending', () => {
		it('should fetch trending topics', async () => {
			const mockResponse = {
				topics: [{ slug: 'test', name: 'Test' }],
				count: 1,
				filters: { themes: null, limit: 10 }
			};
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.getTrending();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/trending',
				expect.objectContaining({
					headers: { 'Content-Type': 'application/json' }
				})
			);
			expect(result).toEqual(mockResponse);
		});

		it('should include theme filter in request', async () => {
			const mockResponse = { topics: [], count: 0, filters: {} };
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			await api.getTrending({ themes: ['esports', 'balance'] });

			expect(mockFetch).toHaveBeenCalledWith(
				expect.stringContaining('theme=esports'),
				expect.any(Object)
			);
		});

		it('should cache responses', async () => {
			const mockResponse = { topics: [], count: 0, filters: {} };
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			await api.getTrending();
			await api.getTrending();

			// Should only fetch once due to cache
			expect(mockFetch).toHaveBeenCalledTimes(1);
		});
	});

	describe('getTopics', () => {
		it('should fetch topics list', async () => {
			const mockResponse = {
				topics: [{ slug: 'balance', name: 'Balance', post_count: 10 }],
				count: 1
			};
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.getTopics();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/topics',
				expect.any(Object)
			);
			expect(result).toEqual(mockResponse);
		});
	});

	describe('getTopic', () => {
		it('should fetch a single topic by slug', async () => {
			const mockTopic = {
				slug: 'balance',
				name: 'Balance',
				sentiment: { positive: 50, neutral: 30, negative: 20 },
				post_count: 100
			};
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockTopic)
			});

			const result = await api.getTopic('balance');

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/topics/balance',
				expect.any(Object)
			);
			expect(result).toEqual(mockTopic);
		});

		it('should encode special characters in slug', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({})
			});

			await api.getTopic('test topic');

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/topics/test%20topic',
				expect.any(Object)
			);
		});
	});

	describe('getSources', () => {
		it('should fetch source distribution', async () => {
			const mockResponse = {
				sources: { youtube: 50, reddit: 30 },
				percentages: { youtube: 62.5, reddit: 37.5 },
				total: 80
			};
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.getSources();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/sources',
				expect.any(Object)
			);
			expect(result).toEqual(mockResponse);
		});
	});

	describe('getPatchPulse', () => {
		it('should fetch patch pulse data', async () => {
			const mockResponse = {
				patch: '14.1',
				topics: [],
				overall_sentiment: { positive: 40, neutral: 40, negative: 20 },
				total_posts: 500,
				last_updated: '2024-01-15T00:00:00Z'
			};
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.getPatchPulse();

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/patch-pulse',
				expect.any(Object)
			);
			expect(result).toEqual(mockResponse);
		});

		it('should include limit parameter', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({})
			});

			await api.getPatchPulse({ limit: 5 });

			expect(mockFetch).toHaveBeenCalledWith(
				expect.stringContaining('limit=5'),
				expect.any(Object)
			);
		});
	});

	describe('submitVote', () => {
		it('should submit thumbs up vote', async () => {
			const mockResponse = { success: true, message: 'Vote recorded' };
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.submitVote({
				topic_slug: 'balance',
				vote_type: 'thumbs_up',
				session_id: 'test-session'
			});

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/feedback/vote',
				expect.objectContaining({
					method: 'POST',
					body: JSON.stringify({
						topic_slug: 'balance',
						vote_type: 'thumbs_up',
						session_id: 'test-session'
					})
				})
			);
			expect(result).toEqual(mockResponse);
		});

		it('should submit thumbs down vote', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({ success: true, message: 'Vote recorded' })
			});

			await api.submitVote({
				topic_slug: 'toxicity',
				vote_type: 'thumbs_down',
				session_id: 'test-session'
			});

			const body = JSON.parse(mockFetch.mock.calls[0][1].body);
			expect(body.vote_type).toBe('thumbs_down');
		});
	});

	describe('submitReport', () => {
		it('should submit a report', async () => {
			const mockResponse = { success: true, message: 'Report submitted' };
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.submitReport({
				topic_slug: 'balance',
				reason: 'misleading',
				details: 'Test details',
				session_id: 'test-session'
			});

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/feedback/report',
				expect.objectContaining({
					method: 'POST'
				})
			);
			expect(result).toEqual(mockResponse);
		});
	});

	describe('submitGeneralFeedback', () => {
		it('should submit general feedback', async () => {
			const mockResponse = { success: true, message: 'Thank you!' };
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.submitGeneralFeedback({
				message: 'Great app!',
				email: 'test@example.com',
				session_id: 'test-session'
			});

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/feedback/general',
				expect.objectContaining({
					method: 'POST'
				})
			);
			expect(result).toEqual(mockResponse);
		});
	});

	describe('getDigestSummary', () => {
		it('should fetch digest summary for slugs', async () => {
			const mockResponse = {
				summary: 'Test summary',
				generated_at: '2024-01-15T00:00:00Z',
				topic_count: 2,
				is_ai_generated: true
			};
			mockFetch.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			const result = await api.getDigestSummary(['balance', 'toxicity']);

			expect(mockFetch).toHaveBeenCalledWith(
				'http://localhost:8000/api/dashboard/digest/summary',
				expect.objectContaining({
					method: 'POST',
					body: JSON.stringify(['balance', 'toxicity'])
				})
			);
			expect(result).toEqual(mockResponse);
		});
	});

	describe('error handling', () => {
		it('should throw error for non-ok response', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 404,
				json: () => Promise.resolve({ detail: 'Not found' })
			});

			await expect(api.getTrending()).rejects.toThrow('Not found');
		});

		it('should handle JSON parse errors in error response', async () => {
			mockFetch.mockResolvedValueOnce({
				ok: false,
				status: 500,
				json: () => Promise.reject(new Error('Invalid JSON'))
			});

			// When JSON parsing fails, it falls back to 'Unknown error'
			await expect(api.getTrending()).rejects.toThrow('Unknown error');
		});
	});

	describe('clearCache', () => {
		it('should clear all cached responses', async () => {
			const mockResponse = { topics: [], count: 0, filters: {} };
			mockFetch.mockResolvedValue({
				ok: true,
				json: () => Promise.resolve(mockResponse)
			});

			await api.getTrending();
			clearCache();
			await api.getTrending();

			// Should fetch twice after cache clear
			expect(mockFetch).toHaveBeenCalledTimes(2);
		});
	});
});
