import { test, expect } from '@playwright/test';

/**
 * TOPIC DETAIL WIRING (UI -> API -> DB).
 *
 * Converted from a render-only spec. The old version navigated to `/topic/...`
 * (singular) -- a route that does not exist; the real route is `/topics/[slug]`.
 * Each test now sources a real slug from the live `/api/dashboard/topics`
 * response, navigates to that topic, asserts the detail API answered, and
 * asserts the real topic data rendered.
 */

/** Load the homepage and return the first real topic slug + name from the DB. */
async function firstRealTopic(page: import('@playwright/test').Page) {
	const topicsPromise = page.waitForResponse(
		(resp) =>
			new URL(resp.url()).pathname.endsWith('/api/dashboard/topics') &&
			resp.request().method() === 'GET',
		{ timeout: 30_000 }
	);
	await page.goto('/');
	const body = await (await topicsPromise).json();
	expect(body.topics.length, 'expected at least one topic in the DB').toBeGreaterThan(0);
	return body.topics[0] as { slug: string; name: string };
}

test.describe('Topic detail wiring (UI -> API -> DB)', () => {
	test('topic page fetches its slug from the real backend and renders it', async ({ page }) => {
		const topic = await firstRealTopic(page);

		const detailPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith(
					`/api/dashboard/topics/${encodeURIComponent(topic.slug)}`
				) && resp.request().method() === 'GET',
			{ timeout: 30_000 }
		);

		await page.goto(`/topics/${topic.slug}`);

		const detailResp = await detailPromise;
		expect(detailResp.ok(), `topic detail API failed: ${detailResp.status()}`).toBeTruthy();

		const detail = await detailResp.json();
		expect(detail.name, 'topic detail returned no name').toBeTruthy();

		// Real data rendered: the heading shows the topic's real name, not an error state.
		const heading = page.locator('h1.topic-name');
		await expect(heading).toBeVisible();
		await expect(heading).toContainText(detail.name);
		await expect(page.getByText(/failed to load|something went wrong/i)).toHaveCount(0);
	});

	test('following a topic persists across reloads (client-side tracking)', async ({ page }) => {
		const topic = await firstRealTopic(page);
		await page.goto(`/topics/${topic.slug}`);
		await expect(page.locator('h1.topic-name')).toBeVisible();

		const followBtn = page.locator('button.follow-btn').first();
		await expect(followBtn).toHaveAttribute('aria-pressed', 'false');

		await followBtn.click();
		await expect(followBtn).toHaveAttribute('aria-pressed', 'true');

		// Persisted to localStorage -> survives a reload (this is what feeds the digest).
		await page.reload();
		await expect(page.locator('h1.topic-name')).toBeVisible();
		await expect(page.locator('button.follow-btn').first()).toHaveAttribute('aria-pressed', 'true');
	});
});
