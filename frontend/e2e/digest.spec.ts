import { test, expect } from '@playwright/test';

/**
 * DIGEST WIRING (UI -> API -> DB).
 *
 * Converted from a render-only spec. The digest is driven by the tracking store
 * (localStorage key `communitypulse:tracked-topics`): each followed slug triggers a
 * GET /api/dashboard/topics/{slug}, and the "AI Summary" toggle triggers a
 * POST /api/dashboard/digest/summary. Tests seed a real slug, then assert those
 * real calls fire and their data renders.
 */

const STORAGE_KEY = 'communitypulse:tracked-topics';

/** Load the homepage and return the first real topic from the DB. */
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

test.describe('Digest wiring (UI -> API -> DB)', () => {
	test('empty state renders when no topics are followed', async ({ page }) => {
		await page.goto('/');
		await page.evaluate((key) => localStorage.removeItem(key), STORAGE_KEY);

		await page.goto('/digest');

		// Genuine empty state -- no network needed, asserted unconditionally.
		await expect(page.getByRole('heading', { name: /no topics in your digest/i })).toBeVisible();
	});

	test('a followed topic loads from the real backend and renders a digest card', async ({
		page
	}) => {
		const topic = await firstRealTopic(page);
		await page.evaluate(
			([key, t]) =>
				localStorage.setItem(
					key as string,
					JSON.stringify([{ ...(t as object), followedAt: new Date().toISOString() }])
				),
			[STORAGE_KEY, topic] as const
		);

		const detailPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith(
					`/api/dashboard/topics/${encodeURIComponent(topic.slug)}`
				) && resp.request().method() === 'GET',
			{ timeout: 30_000 }
		);

		await page.goto('/digest');

		const detailResp = await detailPromise;
		expect(detailResp.ok(), `digest topic fetch failed: ${detailResp.status()}`).toBeTruthy();

		// Real data rendered: the followed-count subtitle and a digest card.
		await expect(page.getByText(/1 topic followed/i)).toBeVisible();
		await expect(page.locator('.digest-grid')).toBeVisible();
	});

	test('AI Summary toggle calls the real summary endpoint and renders the result', async ({
		page
	}) => {
		const topic = await firstRealTopic(page);
		await page.evaluate(
			([key, t]) =>
				localStorage.setItem(
					key as string,
					JSON.stringify([{ ...(t as object), followedAt: new Date().toISOString() }])
				),
			[STORAGE_KEY, topic] as const
		);

		await page.goto('/digest');
		await expect(page.locator('.digest-grid')).toBeVisible();

		const summaryPromise = page.waitForResponse(
			(resp) =>
				new URL(resp.url()).pathname.endsWith('/api/dashboard/digest/summary') &&
				resp.request().method() === 'POST',
			{ timeout: 30_000 }
		);
		await page.getByRole('button', { name: /^ai summary$/i }).click();

		const summaryResp = await summaryPromise;
		expect(summaryResp.ok(), `digest summary POST failed: ${summaryResp.status()}`).toBeTruthy();

		const body = await summaryResp.json();
		expect(body.summary, 'summary text missing').toBeTruthy();

		// The real summary text reached the screen.
		await expect(page.locator('.ai-summary-text')).toBeVisible();
		await expect(page.locator('.ai-summary-text')).not.toBeEmpty();
	});
});
