import nextra from "nextra";

const withNextra = nextra({
  defaultShowCopyCode: true,
  latex: true,
  search: {
    codeblocks: false,
  },
});

const nextConfig = withNextra({
  output: "export",
  reactStrictMode: true,
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  turbopack: {
    resolveAlias: {
      "next-mdx-import-source-file": "./mdx-components.ts",
    },
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
    optimizePackageImports: [],
  },
});

export default nextConfig;
