import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

const isAnalyze = process.env.ANALYZE === 'true';

export default defineConfig({
	plugins: [
		sveltekit(),
		// Bundle analyzer - only when ANALYZE=true
		isAnalyze &&
			visualizer({
				filename: 'stats.html',
				open: true,
				gzipSize: true,
				brotliSize: true
			})
	].filter(Boolean),

	build: {
		// Use esbuild for minification (faster than terser, built-in)
		minify: 'esbuild',

		// Disable source maps in production for smaller bundles
		sourcemap: false,

		// Target modern browsers for smaller output
		target: 'es2020',

		// Rollup options
		rollupOptions: {
			output: {
				// Manual chunks for better caching
				manualChunks: (id) => {
					// Vendor chunk for node_modules
					if (id.includes('node_modules')) {
						// Keep svelte runtime together
						if (id.includes('svelte')) {
							return 'svelte';
						}
						return 'vendor';
					}
				}
			}
		},

		// Increase chunk size warning limit (optional)
		chunkSizeWarningLimit: 500
	},

	// Optimize deps for faster dev
	optimizeDeps: {
		include: ['svelte-persisted-state']
	}
});
