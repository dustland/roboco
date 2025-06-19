import "./globals.css";
import { Head } from "nextra/components";

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
      { url: "/favicon.ico", sizes: "16x16", type: "image/x-icon" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
    apple: "/logo.png",
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

export default function RootLayout({ children }) {
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>{children}</body>
    </html>
  );
}
