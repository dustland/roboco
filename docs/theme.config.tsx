import React from "react";

const config = {
  logo: (
    <>
      <img
        src="/logo.png"
        alt="AgentX"
        height="24"
        width="24"
        style={{ height: "24px", width: "auto" }}
      />
      <span style={{ marginLeft: "8px", fontWeight: 800 }}>AgentX</span>
    </>
  ),
  project: {
    link: "https://github.com/dustland/agentx",
  },
  docsRepositoryBase: "https://github.com/dustland/agentx/tree/main/docs",
  footer: {
    text: <span>MIT {new Date().getFullYear()} © AgentX.</span>,
  },
  sidebar: {
    defaultMenuCollapseLevel: 1,
    autoCollapse: true,
  },
  toc: {
    backToTop: true,
  },
  editLink: {
    text: "Edit this page on GitHub",
  },
  feedback: {
    content: "Question? Give us feedback →",
    labels: "feedback",
  },
  search: {
    placeholder: "Search documentation...",
  },
};

export default config;
