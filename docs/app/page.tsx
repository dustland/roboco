"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Cards, Callout } from "nextra/components";
import { Link } from "nextra-theme-docs";
import { useState, useEffect } from "react";
import {
  Users,
  Wrench,
  Brain,
  Zap,
  BarChart3,
  Settings,
  Target,
  Lock,
  Building,
  Sparkles,
  Rocket,
  Github,
  ArrowRight,
  ChartColumnStacked,
  GraduationCap,
  Bot,
  DollarSign,
} from "lucide-react";

// Floating particles animation
const ParticleField = () => {
  const [particles, setParticles] = useState<
    Array<{ id: number; x: number; y: number; delay: number }>
  >([]);

  useEffect(() => {
    const newParticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 2,
    }));
    setParticles(newParticles);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute w-1 h-1 bg-blue-400/30 rounded-full"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          animate={{
            y: [0, -100, 0],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            delay: particle.delay,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

// Icon wrapper for consistent styling
const IconWrapper = ({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) => <div className={`inline-flex ${className}`}>{children}</div>;

// Optimized typewriter with minimal flickering and single line layout
const AnimatedText = () => {
  const words = ["autonomous", "supervised", "low-cost"];
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    const currentWord = words[currentWordIndex];
    let timeout: NodeJS.Timeout;

    if (!isDeleting && currentText.length < currentWord.length) {
      // Typing
      timeout = setTimeout(() => {
        setCurrentText(currentWord.slice(0, currentText.length + 1));
      }, 100);
    } else if (!isDeleting && currentText.length === currentWord.length) {
      // Pause before deleting
      timeout = setTimeout(() => {
        setIsDeleting(true);
      }, 2000);
    } else if (isDeleting && currentText.length > 0) {
      // Deleting
      timeout = setTimeout(() => {
        setCurrentText(currentText.slice(0, -1));
      }, 50);
    } else if (isDeleting && currentText.length === 0) {
      // Move to next word
      setIsDeleting(false);
      setCurrentWordIndex((prev) => (prev + 1) % words.length);
    }

    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [currentText, isDeleting, currentWordIndex]);

  // Cursor blinking
  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 530);
    return () => clearInterval(cursorInterval);
  }, []);

  // Calculate the width needed for the longest word to prevent layout shifts
  const maxWidth = Math.max(...words.map((word) => word.length)) * 0.6; // Approximate character width in em

  return (
    <div className="flex items-center h-full">
      {/* Fixed width container based on longest word to prevent layout shifts */}
      <div className="flex items-center" style={{ minWidth: `${maxWidth}em` }}>
        <span className="text-white font-mono whitespace-nowrap">
          {currentText}
        </span>
        <span
          className={`inline-block w-0.5 ml-1 bg-emerald-400 transition-opacity duration-150 ${
            showCursor ? "opacity-100" : "opacity-0"
          }`}
          style={{ height: "1em" }}
        />
      </div>
    </div>
  );
};

export default function HomePage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  const features = [
    {
      icon: Users,
      title: "Multi-Agent Orchestration",
      description:
        "Intelligent task distribution and dynamic load balancing for complex multi-agent workflows.",
      href: "/architecture/overview",
    },
    {
      icon: Wrench,
      title: "Extensible Tools",
      description:
        "Native integrations for web APIs, file systems, databases, and custom tool development.",
      href: "/architecture/tool-execution",
    },
    {
      icon: Brain,
      title: "Persistent Memory",
      description:
        "Contextual retention, semantic search, and distributed state persistence across agent networks.",
      href: "/architecture/state-and-context",
    },
    {
      icon: Zap,
      title: "Events",
      description:
        "Real-time coordination, fault tolerance, and scalable inter-agent communication infrastructure.",
      href: "/architecture/communication",
    },
    {
      icon: BarChart3,
      title: "Observability",
      description:
        "Distributed tracing, performance metrics, and intelligent debugging for production deployments.",
      href: "#",
    },
    {
      icon: Settings,
      title: "Configuration-Driven",
      description:
        "Configure agents and teams through simple YAML and Markdown. Almost no code required.",
      href: "#",
    },
  ];

  const useCases = [
    {
      icon: Bot,
      title: "Agentic Apps",
      description:
        "Build intelligent applications where AI agents autonomously handle complex workflows while maintaining human oversight for critical decisions.",
    },
    {
      icon: GraduationCap,
      title: "Academic Research",
      description:
        "Deploy collaborative research teams that systematically gather data, conduct analysis, and synthesize findings across multiple domains and sources.",
    },
    {
      icon: ChartColumnStacked,
      title: "Operational Excellence",
      description:
        "Streamline enterprise operations through intelligent automation, real-time monitoring, and adaptive process optimization at scale.",
    },
    {
      icon: Rocket,
      title: "Creative Innovation",
      description:
        "Accelerate creative processes through AI-assisted ideation, content generation, and iterative design workflows for marketing and product development.",
    },
  ];

  return (
    <div
      className={`
        relative min-h-screen overflow-hidden
        bg-gradient-to-br from-slate-50 via-white to-blue-50 
        dark:from-slate-950 dark:via-slate-900 dark:to-blue-950
      `}
    >
      {/* Animated background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(120,119,198,0.3),rgba(255,255,255,0))]" />
        <ParticleField />
      </div>

      {/* Hero Section */}
      <motion.div
        className="relative z-10"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <div className="mx-auto max-w-7xl px-4 pt-20 pb-16 text-center lg:pt-32">
          <div className="mx-auto max-w-4xl">
            {/* Announcement Badge */}
            <motion.div
              variants={itemVariants}
              className="mb-8 flex justify-center"
            >
              <motion.div
                className="group relative overflow-hidden rounded-full px-4 py-2 text-sm leading-6 text-slate-600 ring-1 ring-slate-900/10 hover:ring-slate-900/20 dark:text-slate-400 dark:ring-slate-800 dark:hover:ring-slate-700 transition-all duration-300"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  layoutId="badge-bg"
                />
                <span className="relative flex items-center gap-2">
                  <Sparkles className="w-4 h-4 mr-2" />
                  Open source multi-agent framework.
                  <Link
                    href="https://github.com/dustland/agentx"
                    className="font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                  >
                    Star on GitHub{" "}
                    <ArrowRight className="w-3 h-3 ml-1 inline" />
                  </Link>
                </span>
              </motion.div>
            </motion.div>

            {/* Main Title */}
            <motion.h1
              variants={itemVariants}
              className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-5xl lg:text-6xl"
            >
              <div className="flex flex-col items-center gap-6">
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 flex-wrap">
                  <span>Build</span>
                  <div className="relative inline-block">
                    <div className="px-4 py-2 bg-slate-950 dark:bg-slate-900 border border-slate-700 dark:border-slate-600 rounded-md font-mono text-2xl sm:text-3xl lg:text-4xl min-w-[280px] h-[60px] flex items-center justify-start shadow-inner">
                      <span className="text-emerald-400 mr-2">$</span>
                      <AnimatedText />
                    </div>
                    {/* Terminal cursor indicator */}
                    <div className="absolute top-1 right-2 w-2 h-2 bg-emerald-400 rounded-full animate-pulse opacity-80"></div>
                  </div>
                  <span>Agentic AI</span>
                </div>
                <motion.div
                  className="text-2xl sm:text-3xl lg:text-4xl"
                  animate={{
                    backgroundPosition: ["0%", "100%", "0%"],
                  }}
                  transition={{
                    duration: 8,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                >
                  <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent bg-[length:200%] animate-gradient">
                    with Multi-Agent Intelligence
                  </span>
                </motion.div>
              </div>
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              variants={itemVariants}
              className="mt-6 text-xl leading-8 text-slate-600 dark:text-slate-300 sm:text-2xl max-w-3xl mx-auto"
            >
              Orchestrate sophisticated multi-agent systems with intelligent
              task distribution, human-in-the-loop control, and cost-optimized
              model integration
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              variants={itemVariants}
              className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6"
            >
              {/* Primary CTA Button */}
              <motion.div
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href="/getting-started"
                  className="group relative inline-flex items-center overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 px-8 py-4 text-lg font-bold text-white shadow-2xl transition-all duration-300 hover:shadow-purple-500/25 hover:from-blue-700 hover:via-purple-700 hover:to-indigo-700"
                >
                  <Sparkles className="mr-3 h-5 w-5 group-hover:rotate-12 transition-transform duration-300" />
                  Get Started
                  <ArrowRight className="ml-3 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                </Link>
              </motion.div>

              {/* Secondary CTA Button */}
              <motion.div
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href="https://github.com/dustland/agentx"
                  className="group inline-flex items-center rounded-xl bg-white/10 dark:bg-slate-800/50 backdrop-blur-xl border border-white/20 dark:border-slate-700/50 px-8 py-4 text-lg font-semibold text-slate-700 dark:text-white shadow-xl hover:bg-white/20 dark:hover:bg-slate-700/50 transition-all duration-300"
                >
                  <Github className="mr-3 h-5 w-5 group-hover:rotate-12 transition-transform duration-300" />
                  View on GitHub
                  <ArrowRight className="ml-3 h-5 w-5 group-hover:translate-x-1 transition-transform duration-300" />
                </Link>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Quick Install Section */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 py-16"
      >
        <div className="mx-auto max-w-4xl px-4">
          <motion.div
            className="rounded-2xl bg-white/80 backdrop-blur-xl p-8 shadow-2xl ring-1 ring-slate-900/5 dark:bg-slate-900/80 dark:ring-slate-800"
            whileHover={{ y: -5 }}
            transition={{ duration: 0.3 }}
          >
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-white">
                Quick Install
              </h2>
              <p className="mt-2 text-slate-600 dark:text-slate-400">
                Get started with AgentX in seconds
              </p>
            </div>

            <div className="space-y-6">
              <motion.div
                className="rounded-lg bg-slate-950 dark:bg-slate-950 p-4 shadow-inner"
                whileHover={{ scale: 1.02 }}
                transition={{ duration: 0.2 }}
              >
                <code className="text-sm text-emerald-400 font-mono block text-center">
                  pip install agentx-py
                </code>
              </motion.div>

              <div className="text-center">
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Or install from source:
                </span>
              </div>

              <motion.div
                className="rounded-lg bg-slate-950 dark:bg-slate-950 p-4 shadow-inner"
                whileHover={{ scale: 1.02 }}
                transition={{ duration: 0.2 }}
              >
                <code className="text-sm text-emerald-400 font-mono block text-center">
                  git clone https://github.com/dustland/agentx.git
                  <br />
                  cd agentx && pip install -e .
                </code>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* The Perfect Balance Section - Moved before Features */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 py-24 bg-gradient-to-br from-slate-100 via-blue-50 to-purple-50 dark:from-slate-800 dark:via-slate-900 dark:to-slate-800 overflow-hidden"
      >
        {/* Background Pattern Effects */}
        <div className="absolute inset-0">
          {/* Floating geometric shapes */}
          <div className="absolute top-20 left-10 w-32 h-32 bg-blue-200/20 rounded-full blur-xl animate-pulse" />
          <div
            className="absolute top-40 right-20 w-24 h-24 bg-purple-200/20 rounded-full blur-lg animate-pulse"
            style={{ animationDelay: "1s" }}
          />
          <div
            className="absolute bottom-32 left-1/4 w-40 h-40 bg-indigo-200/15 rounded-full blur-2xl animate-pulse"
            style={{ animationDelay: "2s" }}
          />
          <div
            className="absolute bottom-20 right-1/3 w-28 h-28 bg-violet-200/20 rounded-full blur-xl animate-pulse"
            style={{ animationDelay: "0.5s" }}
          />

          {/* Subtle grid pattern */}
          <div
            className="absolute inset-0 opacity-5"
            style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, rgba(99, 102, 241, 0.3) 1px, transparent 0)`,
              backgroundSize: "40px 40px",
            }}
          />

          {/* Gradient overlays */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-transparent to-purple-500/5" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-500/3 to-transparent" />
        </div>

        <div className="mx-auto max-w-7xl px-4 relative z-10">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white text-center mb-6">
              Autonomous AI + Human Oversight
            </h2>
            <p className="text-2xl text-slate-700 dark:text-slate-300 max-w-4xl mx-auto leading-relaxed">
              The future of intelligent automation — where AI autonomy
              capabilities seamlessly integrate with human expertise for optimal
              decision-making
            </p>
          </motion.div>

          {/* Three Core Pillars with Glass Effect */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Multi-Agent Autonomy */}
            <motion.div
              className="group relative p-10 h-full min-h-[400px] flex flex-col backdrop-blur-xl shadow-2xl"
              style={{
                background: `linear-gradient(45deg, rgba(59, 130, 246, 0.04), rgba(59, 130, 246, 0.08), rgba(59, 130, 246, 0.02))`,
                border: "1px solid rgba(59, 130, 246, 0.2)",
                backdropFilter: "blur(18px)",
                boxShadow:
                  "0 16px 50px 0 rgba(59, 130, 246, 0.08), inset 0 3px 0 rgba(255,255,255,0.15)",
                transform: "rotate(1deg)",
                borderRadius: "30px 10px 30px 10px",
              }}
              whileHover={{
                scale: 1.02,
                rotate: -0.5,
              }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex flex-col h-full items-center text-center relative z-10">
                <div className="mb-8 mx-auto">
                  <Brain
                    className="w-16 h-16 opacity-80"
                    style={{
                      color: "#3b82f6",
                      filter: "drop-shadow(0 2px 4px rgba(59, 130, 246, 0.2))",
                    }}
                  />
                </div>
                <h3 className="text-2xl font-bold mb-6 text-center text-slate-800 dark:text-white">
                  Multi-Agent Autonomy
                </h3>
                <p className="text-slate-700 dark:text-slate-200 leading-relaxed text-center flex-grow opacity-90">
                  Intelligent orchestration of self-organizing agent networks
                  that coordinate workloads and scale operations autonomously.
                </p>
              </div>
            </motion.div>

            {/* Human in the Loop */}
            <motion.div
              className="group relative p-10 h-full min-h-[400px] flex flex-col backdrop-blur-xl shadow-2xl"
              style={{
                background: `linear-gradient(45deg, rgba(139, 92, 246, 0.04), rgba(139, 92, 246, 0.08), rgba(139, 92, 246, 0.02))`,
                border: "1px solid rgba(139, 92, 246, 0.2)",
                backdropFilter: "blur(18px)",
                boxShadow:
                  "0 16px 50px 0 rgba(139, 92, 246, 0.08), inset 0 3px 0 rgba(255,255,255,0.15)",
                transform: "rotate(-1deg)",
                borderRadius: "30px 10px 30px 10px",
              }}
              whileHover={{
                scale: 1.02,
                rotate: 0.5,
              }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex flex-col h-full items-center text-center relative z-10">
                <div className="mb-8 mx-auto">
                  <Users
                    className="w-16 h-16 opacity-80"
                    style={{
                      color: "#8b5cf6",
                      filter: "drop-shadow(0 2px 4px rgba(139, 92, 246, 0.2))",
                    }}
                  />
                </div>
                <h3 className="text-2xl font-bold mb-6 text-center text-slate-800 dark:text-white">
                  Human in the Loop
                </h3>
                <p className="text-slate-700 dark:text-slate-200 leading-relaxed text-center flex-grow opacity-90">
                  Governance frameworks with human intervention at critical
                  decision points. Define workflows, compliance boundaries, and
                  ethical standards.
                </p>
              </div>
            </motion.div>

            {/* Cost Efficiency */}
            <motion.div
              className="group relative p-10 h-full min-h-[400px] flex flex-col backdrop-blur-xl shadow-2xl"
              style={{
                background: `linear-gradient(45deg, rgba(16, 185, 129, 0.04), rgba(16, 185, 129, 0.08), rgba(16, 185, 129, 0.02))`,
                border: "1px solid rgba(16, 185, 129, 0.2)",
                backdropFilter: "blur(18px)",
                boxShadow:
                  "0 16px 50px 0 rgba(16, 185, 129, 0.08), inset 0 3px 0 rgba(255,255,255,0.15)",
                transform: "rotate(0.5deg)",
                borderRadius: "30px 10px 30px 10px",
              }}
              whileHover={{
                scale: 1.02,
                rotate: -0.5,
              }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex flex-col h-full items-center text-center relative z-10">
                <div className="mb-8 mx-auto">
                  <DollarSign
                    className="w-16 h-16 opacity-80"
                    style={{
                      color: "#10b981",
                      filter: "drop-shadow(0 2px 4px rgba(16, 185, 129, 0.2))",
                    }}
                  />
                </div>
                <h3 className="text-2xl font-bold mb-6 text-center text-slate-800 dark:text-white">
                  Cost Efficiency
                </h3>
                <p className="text-slate-700 dark:text-slate-200 leading-relaxed text-center flex-grow opacity-90">
                  Native support for high-performance, low-cost models like
                  DeepSeek, Claude Haiku, and Gemini Flash. Up to 90% cost
                  reduction with intelligent optimization.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Features Section */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 py-24"
      >
        <div className="mx-auto max-w-7xl px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white text-center mb-6">
              Key Features
            </h2>
            <p className="text-2xl text-slate-600 dark:text-slate-300 max-w-4xl mx-auto leading-relaxed">
              Enterprise-grade capabilities for building sophisticated
              multi-agent architectures
            </p>
          </motion.div>

          {/* Minimal Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <motion.div
                  className="group relative p-6 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-slate-300 dark:hover:border-slate-600 transition-all duration-200"
                  whileHover={{ y: -2 }}
                  transition={{ duration: 0.2 }}
                >
                  {/* Minimal Icon */}
                  <div className="w-12 h-12 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-slate-600 dark:text-slate-400" />
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
                    {feature.description}
                  </p>

                  {/* Minimal CTA */}
                  <Link
                    href={feature.href}
                    className="inline-flex items-center text-xs font-medium text-slate-500 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors group"
                  >
                    Learn More
                    <ArrowRight className="ml-1 h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </motion.div>
              </motion.div>
            ))}
          </div>

          {/* Architecture CTA */}
          <div className="text-center mt-20">
            <p className="text-lg text-slate-600 dark:text-slate-400 mb-8">
              Ready to understand how it all works together?
            </p>
            <Link
              href="/architecture"
              className="inline-flex items-center bg-slate-900 dark:bg-white/20 hover:bg-slate-800 dark:hover:bg-white/30 text-white font-semibold px-8 py-4 rounded-xl transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              <Sparkles className="mr-3 h-5 w-5" />
              Explore the Architecture
              <ArrowRight className="ml-3 h-5 w-5" />
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Suitable For Section - Added after Features */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 py-24"
      >
        <div className="mx-auto max-w-7xl px-4">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white text-center mb-6">
              Suitable For
            </h2>
            <p className="text-2xl text-slate-600 dark:text-slate-300 max-w-4xl mx-auto leading-relaxed">
              Engineered for diverse applications across industries and research
              domains
            </p>
          </motion.div>

          {/* Floating Card Layout */}
          <div className="relative max-w-7xl mx-auto min-h-[600px]">
            {useCases.map((useCase, index) => {
              const positions = [
                { top: "5%", left: "10%", rotate: "-3deg", zIndex: 4 },
                { top: "20%", right: "5%", rotate: "2deg", zIndex: 3 },
                {
                  top: "40%",
                  left: "30%",
                  rotate: "-1deg",
                  zIndex: 2,
                },
                {
                  top: "15%",
                  left: "50%",
                  rotate: "1deg",
                  zIndex: 1,
                },
              ];

              const colors = [
                {
                  bg: "from-blue-50 to-blue-100",
                  border: "border-blue-200",
                  text: "text-blue-900",
                  accent: "bg-blue-500",
                },
                {
                  bg: "from-purple-50 to-purple-100",
                  border: "border-purple-200",
                  text: "text-purple-900",
                  accent: "bg-purple-500",
                },
                {
                  bg: "from-emerald-50 to-emerald-100",
                  border: "border-emerald-200",
                  text: "text-emerald-900",
                  accent: "bg-emerald-500",
                },
                {
                  bg: "from-orange-50 to-orange-100",
                  border: "border-orange-200",
                  text: "text-orange-900",
                  accent: "bg-orange-500",
                },
              ];

              return (
                <motion.div
                  key={useCase.title}
                  className="absolute w-96 h-80"
                  style={{
                    top: positions[index].top,
                    left: positions[index].left,
                    right: positions[index].right,
                    transform: `rotate(${positions[index].rotate})`,
                    zIndex: positions[index].zIndex,
                  }}
                  initial={{ opacity: 0, y: 50, rotate: 0 }}
                  whileInView={{
                    opacity: 1,
                    y: 0,
                    rotate: parseInt(
                      positions[index].rotate.replace("deg", "")
                    ),
                  }}
                  viewport={{ once: true }}
                  transition={{
                    duration: 0.8,
                    delay: index * 0.2,
                    type: "spring",
                  }}
                  whileHover={{
                    scale: 1.08,
                    rotate: 0,
                    zIndex: 20,
                    y: -10,
                  }}
                >
                  <div
                    className="relative w-full h-full backdrop-blur-xl rounded-3xl p-8 shadow-2xl"
                    style={{
                      background:
                        colors[index].accent
                          .replace("bg-", "")
                          .replace("-500", "") === "blue"
                          ? `linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.05))`
                          : colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "purple"
                          ? `linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.05))`
                          : colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "emerald"
                          ? `linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(16, 185, 129, 0.05))`
                          : `linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(249, 115, 22, 0.05))`,
                      border:
                        colors[index].accent
                          .replace("bg-", "")
                          .replace("-500", "") === "blue"
                          ? "1px solid rgba(59, 130, 246, 0.3)"
                          : colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "purple"
                          ? "1px solid rgba(139, 92, 246, 0.3)"
                          : colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "emerald"
                          ? "1px solid rgba(16, 185, 129, 0.3)"
                          : "1px solid rgba(249, 115, 22, 0.3)",
                      backdropFilter: "blur(20px)",
                      boxShadow:
                        colors[index].accent
                          .replace("bg-", "")
                          .replace("-500", "") === "blue"
                          ? "0 8px 32px 0 rgba(59, 130, 246, 0.2), inset 0 1px 0 rgba(255,255,255,0.3)"
                          : colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "purple"
                          ? "0 8px 32px 0 rgba(139, 92, 246, 0.2), inset 0 1px 0 rgba(255,255,255,0.3)"
                          : colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "emerald"
                          ? "0 8px 32px 0 rgba(16, 185, 129, 0.2), inset 0 1px 0 rgba(255,255,255,0.3)"
                          : "0 8px 32px 0 rgba(249, 115, 22, 0.2), inset 0 1px 0 rgba(255,255,255,0.3)",
                    }}
                  >
                    {/* Corner accent with glass effect */}
                    <div
                      className="absolute top-0 right-0 w-20 h-20 rounded-bl-3xl rounded-tr-3xl"
                      style={{
                        background:
                          colors[index].accent
                            .replace("bg-", "")
                            .replace("-500", "") === "blue"
                            ? `linear-gradient(135deg, rgba(59, 130, 246, 0.25), transparent)`
                            : colors[index].accent
                                .replace("bg-", "")
                                .replace("-500", "") === "purple"
                            ? `linear-gradient(135deg, rgba(139, 92, 246, 0.25), transparent)`
                            : colors[index].accent
                                .replace("bg-", "")
                                .replace("-500", "") === "emerald"
                            ? `linear-gradient(135deg, rgba(16, 185, 129, 0.25), transparent)`
                            : `linear-gradient(135deg, rgba(249, 115, 22, 0.25), transparent)`,
                      }}
                    />

                    {/* Engraved Icon */}
                    <div className="mb-6">
                      <useCase.icon
                        className="w-12 h-12 opacity-70"
                        style={{
                          color:
                            colors[index].accent
                              .replace("bg-", "")
                              .replace("-500", "") === "blue"
                              ? "#3b82f6"
                              : colors[index].accent
                                  .replace("bg-", "")
                                  .replace("-500", "") === "purple"
                              ? "#8b5cf6"
                              : colors[index].accent
                                  .replace("bg-", "")
                                  .replace("-500", "") === "emerald"
                              ? "#10b981"
                              : "#f97316",
                          filter:
                            "drop-shadow(0 1px 2px rgba(0,0,0,0.1)) drop-shadow(0 -1px 1px rgba(255,255,255,0.3))",
                        }}
                      />
                    </div>

                    {/* Content with glass-friendly colors */}
                    <h3 className="text-2xl font-bold mb-4 text-slate-800 dark:text-white">
                      {useCase.title}
                    </h3>
                    <p className="text-slate-700 dark:text-slate-200 text-base leading-relaxed opacity-90">
                      {useCase.description}
                    </p>

                    {/* Glass decorative dots */}
                    <div className="absolute bottom-6 right-6 flex space-x-1.5">
                      <div
                        className="w-2 h-2 rounded-full backdrop-blur-sm border border-white/30"
                        style={{
                          background: `linear-gradient(135deg, rgba(255,255,255,0.3), rgba(255,255,255,0.1))`,
                        }}
                      />
                      <div
                        className="w-2 h-2 rounded-full backdrop-blur-sm border border-white/30"
                        style={{
                          background: `linear-gradient(135deg, rgba(255,255,255,0.4), rgba(255,255,255,0.2))`,
                        }}
                      />
                      <div
                        className="w-2 h-2 rounded-full backdrop-blur-sm border border-white/30"
                        style={{
                          background: `linear-gradient(135deg, rgba(255,255,255,0.5), rgba(255,255,255,0.3))`,
                        }}
                      />
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </motion.div>

      {/* Final CTA */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 py-24"
      >
        <div className="mx-auto max-w-4xl px-4 text-center">
          <motion.div
            className="rounded-3xl bg-gradient-to-br from-blue-600 to-purple-600 p-12 shadow-2xl"
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to Deploy Intelligent Agents?
            </h2>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Join industry leaders building the next generation of AI systems
              with true autonomy
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href="/architecture"
                  className="inline-flex items-center bg-white text-blue-600 font-semibold py-3 px-8 rounded-lg shadow-lg hover:bg-blue-50 transition-colors duration-200"
                >
                  Read the Docs
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </motion.div>
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link
                  href="https://github.com/dustland/agentx/tree/main/examples"
                  className="inline-flex items-center text-white font-semibold py-3 px-8 rounded-lg border border-white/20 hover:bg-white/10 transition-colors duration-200"
                >
                  View Examples
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
