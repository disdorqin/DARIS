// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import rehypeMermaid from 'rehype-mermaid';

export default defineConfig({
	site: 'https://arise-ai.dev',
	markdown: {
		rehypePlugins: [[rehypeMermaid, { strategy: 'inline-svg', dark: true }]],
	},
	integrations: [
		starlight({
			title: 'ARISE',
			tagline: 'Agents that create their own tools',
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/abekek/arise' },
			],
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Installation', slug: 'getting-started/installation' },
						{ label: 'Quick Start', slug: 'getting-started/quickstart' },
						{ label: 'How It Works', slug: 'getting-started/how-it-works' },
					],
				},
				{
					label: 'Guide',
					items: [
						{ label: 'Reward Functions', slug: 'guide/rewards' },
						{ label: 'Safety & Validation', slug: 'guide/safety' },
						{ label: 'Distributed Mode', slug: 'guide/distributed' },
						{ label: 'Skill Registry', slug: 'guide/registry' },
						{ label: 'Dashboard', slug: 'guide/dashboard' },
						{ label: 'Console (Web UI)', slug: 'guide/console' },
					{ label: 'Framework Adapters', slug: 'guide/adapters' },
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'CLI', slug: 'reference/cli' },
						{ label: 'API - ARISE', slug: 'reference/api-arise' },
						{ label: 'API - Config', slug: 'reference/api-config' },
						{ label: 'API - Types', slug: 'reference/api-types' },
					],
				},
				{
					label: 'Benchmarks',
					slug: 'benchmarks',
				},
			],
		}),
	],
});
