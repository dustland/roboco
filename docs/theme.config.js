export default {
  github: "https://github.com/dustland/agentx",
  docsRepositoryBase: "https://github.com/dustland/agentx/blob/main/docs",
  titleSuffix: " – AgentX",
  logo: (
    <>
      <span className="mr-2 font-extrabold hidden md:inline">AgentX</span>
      <span className="text-gray-600 font-normal hidden md:inline">
        The next-generation framework for autonomous multi-agent systems
      </span>
    </>
  ),
  head: (
    <>
      <meta name="msapplication-TileColor" content="#ffffff" />
      <meta name="theme-color" content="#ffffff" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta httpEquiv="Content-Language" content="en" />
      <meta name="description" content="AgentX - Build, orchestrate, and scale AI agents with unprecedented simplicity and power" />
      <meta name="og:description" content="AgentX - Build, orchestrate, and scale AI agents with unprecedented simplicity and power" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site:domain" content="dustland.github.io" />
      <meta name="twitter:url" content="https://dustland.github.io/agentx" />
      <meta name="og:title" content="AgentX: Next-generation multi-agent framework" />
      <meta name="apple-mobile-web-app-title" content="AgentX" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
    </>
  ),
  search: true,
  prevLinks: true,
  nextLinks: true,
  footer: true,
  footerEditLink: "Edit this page on GitHub",
  footerText: <>MIT {new Date().getFullYear()} © Dustland Team.</>,
  unstable_faviconGlyph: "🤖",
  primaryHue: 220, // Indigo color matching your brand
  primarySaturation: 100,
};
