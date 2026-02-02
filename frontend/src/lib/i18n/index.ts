/**
 * i18n configuration for CommunityPulse Dashboard
 *
 * Uses svelte-i18n for internationalization.
 * Currently English only, prepared for future localization.
 */

import { browser } from '$app/environment';
import { init, register, locale, getLocaleFromNavigator } from 'svelte-i18n';

// Register available locales
register('en', () => import('./locales/en.json'));

// Future locales (uncomment when translations are ready)
// register('ko', () => import('./locales/ko.json'));
// register('zh', () => import('./locales/zh.json'));
// register('ja', () => import('./locales/ja.json'));

// Default locale
const defaultLocale = 'en';

// Supported locales
export const supportedLocales = ['en'] as const;
export type SupportedLocale = (typeof supportedLocales)[number];

// Initialize i18n
export function initI18n() {
	init({
		fallbackLocale: defaultLocale,
		initialLocale: browser ? getLocaleFromNavigator() || defaultLocale : defaultLocale,
	});
}

// Set locale programmatically
export function setLocale(newLocale: SupportedLocale) {
	locale.set(newLocale);
}

// Get current locale
export function getLocale(): string {
	let current = defaultLocale;
	locale.subscribe((value) => {
		if (value) current = value;
	})();
	return current;
}

// Re-export commonly used functions
export { _, t, locale, isLoading } from 'svelte-i18n';
