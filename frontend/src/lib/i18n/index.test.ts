/**
 * Tests for i18n configuration.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock svelte-i18n before importing
vi.mock('svelte-i18n', () => ({
	init: vi.fn(),
	register: vi.fn(),
	getLocaleFromNavigator: vi.fn(() => 'en'),
	locale: {
		subscribe: vi.fn((fn: (value: string) => void) => {
			fn('en');
			return () => {};
		}),
		set: vi.fn()
	},
	_: { subscribe: vi.fn() },
	t: { subscribe: vi.fn() },
	isLoading: { subscribe: vi.fn() }
}));

// Mock $app/environment
vi.mock('$app/environment', () => ({
	browser: true
}));

describe('i18n configuration', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should export supportedLocales with en', async () => {
		const { supportedLocales } = await import('./index');
		expect(supportedLocales).toContain('en');
	});

	it('should export initI18n function', async () => {
		const { initI18n } = await import('./index');
		expect(typeof initI18n).toBe('function');
	});

	it('should export setLocale function', async () => {
		const { setLocale } = await import('./index');
		expect(typeof setLocale).toBe('function');
	});

	it('should export getLocale function', async () => {
		const { getLocale } = await import('./index');
		expect(typeof getLocale).toBe('function');
	});

	it('should return locale from getLocale', async () => {
		const { getLocale } = await import('./index');
		const locale = getLocale();
		expect(typeof locale).toBe('string');
	});
});
