import nextra from "nextra";

const withNextra = nextra({
  latex: true,
  defaultShowCopyCode: true,
  search: {
    codeblocks: false,
  },
  contentDirBasePath: "/",
});

// Use basePath only for GitHub Pages deployment
const isGitHubPages = process.env.GITHUB_ACTIONS === "true";

export default withNextra({
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  ...(isGitHubPages && {
    basePath: "/agentx",
    assetPrefix: "/agentx",
  }),
  images: {
    unoptimized: true,
  },
  eslint: {
    // Ignore ESLint errors during builds for now
    ignoreDuringBuilds: true,
  },
  webpack(config) {
    // rule.exclude doesn't work starting from Next.js 15
    const { test: _test, ...imageLoaderOptions } = config.module.rules.find(
      (rule) => rule.test?.test?.(".svg")
    );
    config.module.rules.push({
      test: /\.svg$/,
      oneOf: [
        {
          resourceQuery: /svgr/,
          use: ["@svgr/webpack"],
        },
        imageLoaderOptions,
      ],
    });
    return config;
  },
  experimental: {
    optimizePackageImports: ["nextra-theme-docs"],
  },
});
