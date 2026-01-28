/**
 * Feedback store with localStorage persistence
 * Tracks user votes to prevent double-voting
 */
import { persistedState } from 'svelte-persisted-state';

/** Vote type for feedback */
export type VoteType = 'thumbs_up' | 'thumbs_down';

/** Stored vote entry */
export interface StoredVote {
	slug: string;
	vote: VoteType;
	votedAt: string; // ISO date string
}

/** Key for localStorage */
const STORAGE_KEY = 'communitypulse:feedback-votes';

/**
 * Persisted state for user votes
 * Auto-syncs with localStorage and across tabs
 */
export const feedbackVotes = persistedState<StoredVote[]>(STORAGE_KEY, []);

/**
 * Generate a session ID for anonymous feedback
 * Uses localStorage to persist across sessions
 */
function getSessionId(): string {
	const SESSION_KEY = 'communitypulse:session-id';
	let sessionId = localStorage.getItem(SESSION_KEY);
	if (!sessionId) {
		sessionId = crypto.randomUUID();
		localStorage.setItem(SESSION_KEY, sessionId);
	}
	return sessionId;
}

/**
 * Get session ID (exported for API calls)
 */
export function getAnonymousSessionId(): string {
	return getSessionId();
}

/**
 * Record a vote for a topic
 */
export function recordVote(slug: string, vote: VoteType): void {
	// Remove any existing vote for this topic
	const existing = feedbackVotes.current.filter((v: StoredVote) => v.slug !== slug);
	feedbackVotes.current = [
		...existing,
		{ slug, vote, votedAt: new Date().toISOString() }
	];
}

/**
 * Get the vote for a topic (if any)
 */
export function getVote(slug: string): VoteType | null {
	const vote = feedbackVotes.current.find((v: StoredVote) => v.slug === slug);
	return vote?.vote ?? null;
}

/**
 * Check if user has voted on a topic
 */
export function hasVoted(slug: string): boolean {
	return feedbackVotes.current.some((v: StoredVote) => v.slug === slug);
}
