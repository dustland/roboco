import { Layout, Navbar } from "nextra-theme-docs";
import { getPageMap } from "nextra/page-map";

const navbar = (
  <Navbar
    logo={
      <div>
        <img
          src="/logo.png"
          alt="AgentX"
          height="24"
          width="24"
          style={{
            height: "24px",
            width: "auto",
            display: "inline",
            marginRight: "8px",
          }}
        />
        <b>AgentX</b>{" "}
        <span style={{ opacity: "60%" }}>Multi-Agent Framework</span>
      </div>
    }
    projectLink="https://github.com/dustland/agentx"
  />
);

export default async function DocsLayout({ children }) {
  const pageMap = await getPageMap();
  return (
    <Layout
      navbar={navbar}
      editLink="Edit this page on GitHub"
      docsRepositoryBase="https://github.com/dustland/agentx/tree/main/docs"
      sidebar={{ defaultMenuCollapseLevel: 1 }}
      pageMap={pageMap}
    >
      {children}
    </Layout>
  );
}
