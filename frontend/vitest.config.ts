import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST })],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		globals: true,
		environment: 'jsdom',
		setupFiles: ['src/tests/setup.ts'],
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html'],
			exclude: ['node_modules/', 'src/tests/', '**/*.d.ts', '**/*.config.*']
		},
		alias: {
			$lib: new URL('./src/lib', import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1'),
			$app: new URL('./src/tests/mocks/app', import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1')
		}
	},
	resolve: {
		alias: {
			$lib: new URL('./src/lib', import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1'),
			$app: new URL('./src/tests/mocks/app', import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1')
		}
	}
});
