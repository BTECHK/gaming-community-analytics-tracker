import { test, expect } from '@playwright/test';

/**
 * DASHBOARD WIRING (UI -> API -> DB).
 *
 * Converted from a render-only spec to the canonical anti-phantom pattern
 * (see wiring.smoke.spec.ts): every test awaits the real network request the
 * page makes, asserts the API answered, and asserts the real response data
 * reached the DOM -- no `if (await el.isVisible())` escape hatches.
 *
 * The homepage's "Trending Topics" grid is intentionally NOT asserted here:
 * `/api/dashboard/trending` is time-windowed (period_end within N days) and is
 * empty whenever the aggregated data is older than the window. The Stats Banner,
 * by contrast, is backed by `/api/dashboard/stats` (no time filter) and is the
 * homepage's reliable real-data element.
 */

test.describe('Dashboard wiring (UI -> API -> DB)', () => {
	test('stats banner renders real data from the live /stats endpoint', async ({ page }) => {
		const statsPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/dashboard/stats') &&
				resp.request().method() === 'GET',
			{ timeout: 30_000 }
		);

		await page.goto('/');

		const statsResp = await statsPromise;
		expect(statsResp.ok(), `stats API failed: ${statsResp.status()}`).toBeTruthy();

		const stats = await statsResp.json();
		// Real, non-empty data straight from the DB.
		expect(typeof stats.posts_analyzed, 'posts_analyzed missing').toBe('number');
		expect(stats.posts_analyzed, 'expected analyzed posts in the DB').toBeGreaterThan(0);

		// And that exact value reached the screen (data -> DOM binding is wired).
		const banner = page.locator('.stats-banner');
		await expect(banner).toBeVisible();
		await expect(banner).toContainText(stats.posts_analyzed.toLocaleString());
		await expect(banner).toContainText('Active Topics');
	});

	test('homepage fans out to the real topics endpoint with DB-backed slugs', async ({ page }) => {
		const topicsPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/dashboard/topics') &&
				resp.request().method() === 'GET',
			{ timeout: 30_000 }
		);

		await page.goto('/');

		const topicsResp = await topicsPromise;
		expect(topicsResp.ok(), `topics API failed: ${topicsResp.status()}`).toBeTruthy();

		const body = await topicsResp.json();
		expect(Array.isArray(body.topics), 'topics is not an array').toBeTruthy();
		expect(body.topics.length, 'expected topics in the DB').toBeGreaterThan(0);
		// Every topic carries a real slug we can navigate to (used by topics.spec).
		expect(typeof body.topics[0].slug).toBe('string');
		expect(body.topics[0].slug.length).toBeGreaterThan(0);
	});
});
