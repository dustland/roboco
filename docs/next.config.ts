import nextra from "nextra";
import bundleAnalyzer from "@next/bundle-analyzer";

const withNextra = nextra({
  latex: true,
  search: {
    codeblocks: false,
  },
});

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

const nextConfig = withBundleAnalyzer(
  withNextra({
    output: "export",
    reactStrictMode: true,
    eslint: {
      // Warning: This allows production builds to successfully complete even if
      // your project has ESLint errors.
      ignoreDuringBuilds: true,
    },
    i18n: {
      locales: ["en", "zh"],
      defaultLocale: "zh",
    },
    redirects: async () => [
      {
        source: "/docs",
        destination: "/docs/getting-started",
        statusCode: 302,
      },
    ],
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
  })
);

export default nextConfig;
