import { Link } from "nextra-theme-docs";

// Custom icons as SVG components
const ArrowRightIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
    />
  </svg>
);

const GitHubLogoIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
  </svg>
);

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Hero Section */}
      <div className="relative">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,#fff,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]" />

        <div className="relative mx-auto max-w-7xl px-4 pt-20 pb-16 text-center lg:pt-32">
          <div className="mx-auto max-w-4xl">
            <div className="mb-8 flex justify-center">
              <div className="relative rounded-full px-3 py-1 text-sm leading-6 text-gray-600 ring-1 ring-gray-900/10 hover:ring-gray-900/20 dark:text-gray-400 dark:ring-gray-800 dark:hover:ring-gray-700">
                Open source multi-agent framework.{" "}
                <Link
                  href="https://github.com/dustland/agentx"
                  className="font-semibold text-blue-600 dark:text-blue-400"
                >
                  <span className="absolute inset-0" aria-hidden="true" />
                  Star on GitHub <span aria-hidden="true">&rarr;</span>
                </Link>
              </div>
            </div>

            <h1 className="text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-7xl lg:text-8xl">
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
                AgentX
              </span>
            </h1>

            <p className="mt-6 text-xl leading-8 text-gray-600 dark:text-gray-300 sm:text-2xl">
              Build, observe, and orchestrate{" "}
              <span className="font-semibold text-gray-900 dark:text-white">
                autonomous multi-agent systems
              </span>{" "}
              with ease
            </p>

            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/architecture"
                className="group rounded-md bg-blue-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-all duration-200"
              >
                Get started
                <ArrowRightIcon className="ml-2 inline h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="https://github.com/dustland/agentx"
                className="group flex items-center text-base font-semibold leading-6 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                <GitHubLogoIcon className="mr-2 h-5 w-5" />
                View on GitHub
                <ArrowRightIcon className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Install Section */}
      <div className="relative py-16">
        <div className="mx-auto max-w-4xl px-4">
          <div className="rounded-2xl bg-white/50 p-8 shadow-xl ring-1 ring-gray-900/5 backdrop-blur dark:bg-gray-900/50 dark:ring-gray-800">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Quick Install
              </h2>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Get started with AgentX in seconds
              </p>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg bg-gray-950 p-4 text-center">
                <code className="text-sm text-gray-100 font-mono">
                  pip install agentx
                </code>
              </div>

              <div className="text-center text-sm text-gray-500 dark:text-gray-400">
                Or install from source:
              </div>

              <div className="rounded-lg bg-gray-950 p-4 text-center">
                <code className="text-sm text-gray-100 font-mono block">
                  git clone https://github.com/dustland/agentx.git
                  <br />
                  cd agentx && pip install -e .
                </code>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              Everything you need to build intelligent agents
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-gray-300">
              A comprehensive framework designed for production-ready
              multi-agent systems
            </p>
          </div>

          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {[
                {
                  icon: "🤝",
                  name: "Multi-Agent Orchestration",
                  description:
                    "Coordinate multiple AI agents seamlessly with intelligent task distribution and collaboration patterns.",
                  href: "/architecture/overview",
                },
                {
                  icon: "🛠️",
                  name: "Rich Tool Ecosystem",
                  description:
                    "Built-in tools for web search, file operations, memory management, and easy integration of custom tools.",
                  href: "/architecture/tool-execution",
                },
                {
                  icon: "🧠",
                  name: "Advanced Memory",
                  description:
                    "Persistent and contextual memory systems that enable agents to maintain state across long-running tasks.",
                  href: "/architecture/state-and-context",
                },
                {
                  icon: "⚡",
                  name: "Event-Driven Architecture",
                  description:
                    "Real-time communication and coordination between agents with a robust event system.",
                  href: "/architecture/communication",
                },
                {
                  icon: "📊",
                  name: "Built-in Observability",
                  description:
                    "Monitor, debug, and analyze agent behavior with comprehensive logging and visualization tools.",
                  href: "#",
                },
                {
                  icon: "🔧",
                  name: "Flexible Configuration",
                  description:
                    "YAML-based configuration system for easy setup and management of complex agent teams.",
                  href: "#",
                },
              ].map((feature) => (
                <div key={feature.name} className="group">
                  <Link href={feature.href} className="block">
                    <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      <span className="text-2xl">{feature.icon}</span>
                      {feature.name}
                    </dt>
                    <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600 dark:text-gray-300">
                      <p className="flex-auto">{feature.description}</p>
                    </dd>
                  </Link>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative isolate">
        <div className="mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              Ready to get started?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-gray-600 dark:text-gray-300">
              Explore our documentation and start building with AgentX today.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/architecture"
                className="rounded-md bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 text-base font-semibold text-white shadow-sm hover:from-blue-700 hover:to-purple-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-all duration-200"
              >
                Read the docs
              </Link>
              <Link
                href="https://github.com/dustland/agentx/tree/main/examples"
                className="text-base font-semibold leading-6 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
              >
                View examples <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
