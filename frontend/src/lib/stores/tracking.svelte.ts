/**
 * Topic tracking store with localStorage persistence
 * Uses svelte-persisted-state for Svelte 5 runes compatibility
 */
import { persistedState } from 'svelte-persisted-state';

/** Tracked topic entry */
export interface TrackedTopic {
	slug: string;
	name: string;
	followedAt: string; // ISO date string
}

/** Key for localStorage */
const STORAGE_KEY = 'communitypulse:tracked-topics';

/**
 * Persisted state for tracked topics
 * Auto-syncs with localStorage and across tabs
 */
export const trackedTopics = persistedState<TrackedTopic[]>(STORAGE_KEY, []);

/**
 * Follow a topic
 */
export function followTopic(slug: string, name: string): void {
	const existing = trackedTopics.current.find((t: TrackedTopic) => t.slug === slug);
	if (existing) return;
	trackedTopics.current = [
		...trackedTopics.current,
		{ slug, name, followedAt: new Date().toISOString() }
	];
}

/**
 * Unfollow a topic
 */
export function unfollowTopic(slug: string): void {
	trackedTopics.current = trackedTopics.current.filter((t: TrackedTopic) => t.slug !== slug);
}

/**
 * Check if a topic is followed
 */
export function isFollowing(slug: string): boolean {
	return trackedTopics.current.some((t: TrackedTopic) => t.slug === slug);
}

/**
 * Get count of followed topics
 */
export function getFollowedCount(): number {
	return trackedTopics.current.length;
}
