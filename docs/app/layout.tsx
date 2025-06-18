import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    template: "%s | AgentX Docs",
    default: "AgentX Docs",
  },
  description:
    "An open-source framework for building, observing, and orchestrating autonomous multi-agent systems.",
  metadataBase: new URL("https://dustland.github.io/agentx"),
  appleWebApp: {
    title: "AgentX Docs",
  },
  other: {
    "msapplication-TileColor": "#fff",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
