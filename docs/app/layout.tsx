import "./globals.css";
import { Head } from "nextra/components";
import { Layout, Navbar } from "nextra-theme-docs";
import { getPageMap } from "nextra/page-map";
import Image from "next/image";

// Get the base path for favicon assets in metadata
const basePath =
  process.env.NODE_ENV === "production" && process.env.GITHUB_ACTIONS === "true"
    ? "/agentx"
    : "";

const navbar = (
  <Navbar
    logo={
      <div>
        <Image
          src="/logo.png"
          alt="AgentX"
          height={24}
          width={24}
          style={{
            height: "24px",
            width: "auto",
            display: "inline",
            marginRight: "8px",
          }}
        />
        <b>AgentX</b>
      </div>
    }
    projectLink="https://github.com/dustland/agentx"
  />
);

export const metadata = {
  metadataBase: new URL("https://dustland.github.io/agentx"),
  title: {
    default: "AgentX – Multi-Agent Framework",
    template: "%s | AgentX",
  },
  description:
    "An open-source framework for building, observing, and orchestrating autonomous multi-agent systems.",
  keywords: [
    "AgentX",
    "Multi-Agent",
    "AI",
    "Framework",
    "Autonomous",
    "Python",
    "LLM",
    "Agent Orchestration",
  ],
  applicationName: "AgentX",
  generator: "Next.js",
  appleWebApp: {
    title: "AgentX",
  },
  icons: {
    icon: [
      { url: `${basePath}/favicon.ico`, sizes: "16x16", type: "image/x-icon" },
      {
        url: `${basePath}/favicon-16x16.png`,
        sizes: "16x16",
        type: "image/png",
      },
      {
        url: `${basePath}/favicon-32x32.png`,
        sizes: "32x32",
        type: "image/png",
      },
    ],
    shortcut: `${basePath}/favicon.ico`,
    apple: `${basePath}/logo.png`,
  },
  openGraph: {
    url: "https://dustland.github.io/agentx",
    siteName: "AgentX",
    locale: "en_US",
    type: "website",
  },
  other: {
    "msapplication-TileColor": "#fff",
  },
  alternates: {
    canonical: "https://dustland.github.io/agentx",
  },
};

export default async function RootLayout({ children }) {
  const pageMap = await getPageMap();
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <Layout
          navbar={navbar}
          editLink="Edit this page on GitHub"
          docsRepositoryBase="https://github.com/dustland/agentx/tree/main/docs"
          sidebar={{ defaultMenuCollapseLevel: 1 }}
          pageMap={pageMap}
        >
          {children}
        </Layout>
      </body>
    </html>
  );
}
