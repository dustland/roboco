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
        "Coordinate multiple AI agents seamlessly with intelligent task distribution and collaboration patterns.",
      href: "/architecture/overview",
    },
    {
      icon: Wrench,
      title: "Rich Tool Ecosystem",
      description:
        "Built-in tools for web search, file operations, memory management, and easy integration of custom tools.",
      href: "/architecture/tool-execution",
    },
    {
      icon: Brain,
      title: "Advanced Memory",
      description:
        "Persistent and contextual memory systems that enable agents to maintain state across long-running tasks.",
      href: "/architecture/state-and-context",
    },
    {
      icon: Zap,
      title: "Event-Driven Architecture",
      description:
        "Real-time communication and coordination between agents with a robust event system.",
      href: "/architecture/communication",
    },
    {
      icon: BarChart3,
      title: "Built-in Observability",
      description:
        "Monitor, debug, and analyze agent behavior with comprehensive logging and visualization tools.",
      href: "#",
    },
    {
      icon: Settings,
      title: "Configuration-as-Code",
      description:
        "Define your entire agent ecosystem in code. Version-controlled YAML configs, reproducible deployments, and GitOps-ready workflows.",
      href: "#",
    },
  ];

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-blue-950 overflow-hidden">
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
                <span className="relative flex items-center">
                  <Sparkles className="w-4 h-4 mr-2" />
                  Open source multi-agent framework.{" "}
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
                  <span>Build a</span>
                  <div className="relative inline-block">
                    <div className="px-4 py-2 bg-slate-950 dark:bg-slate-900 border border-slate-700 dark:border-slate-600 rounded-md font-mono text-2xl sm:text-3xl lg:text-4xl min-w-[280px] h-[60px] flex items-center justify-start shadow-inner">
                      <span className="text-emerald-400 mr-2">$</span>
                      <AnimatedText />
                    </div>
                    {/* Terminal cursor indicator */}
                    <div className="absolute top-1 right-2 w-2 h-2 bg-emerald-400 rounded-full animate-pulse opacity-80"></div>
                  </div>
                  <span>Agentic App</span>
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
              Coordinate multiple AI agents seamlessly with intelligent task
              distribution, human oversight, and cost-effective DeepSeek
              integration
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
            <h2 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white flex items-center justify-center mb-6">
              <Sparkles className="w-10 h-10 mr-4 text-blue-500" />
              Key Features
            </h2>
            <p className="text-2xl text-slate-600 dark:text-slate-300 max-w-4xl mx-auto leading-relaxed">
              Everything you need to build production-ready multi-agent systems
            </p>
          </motion.div>

          {/* Unified Grid Layout */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
              >
                <motion.div
                  className="group relative overflow-hidden rounded-2xl bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl p-8 shadow-xl border border-slate-200/50 dark:border-slate-700/50 h-80 flex flex-col"
                  whileHover={{ y: -8, scale: 1.02 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Icon */}
                  <div className="flex-shrink-0 w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mb-6">
                    <feature.icon className="w-8 h-8 text-white" />
                  </div>

                  {/* Content */}
                  <div className="flex-grow flex flex-col">
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">
                      {feature.title}
                    </h3>
                    <p className="text-slate-600 dark:text-slate-300 leading-relaxed mb-6 flex-grow">
                      {feature.description}
                    </p>

                    {/* CTA Link */}
                    <Link
                      href={feature.href}
                      className="inline-flex items-center text-blue-600 dark:text-blue-400 font-medium hover:text-blue-700 dark:hover:text-blue-300 transition-colors group mt-auto"
                    >
                      Learn More
                      <ArrowRight className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                    </Link>
                  </div>
                </motion.div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Why Choose Section - Key Differentiator */}
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="relative z-10 py-32 bg-gradient-to-r from-slate-900 via-purple-900 to-slate-900 dark:from-slate-950 dark:via-purple-950 dark:to-slate-950"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.3),transparent_50%)]" />
        <div className="mx-auto max-w-7xl px-4 relative z-10">
          <motion.div
            className="text-center mb-20"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-5xl md:text-6xl font-bold text-white flex items-center justify-center mb-6">
              <Users className="w-12 h-12 mr-4 text-purple-400" />
              The Perfect Balance
            </h2>
            <p className="text-2xl text-purple-200 max-w-4xl mx-auto leading-relaxed">
              <span className="text-white font-semibold">Autonomous AI</span>{" "}
              meets{" "}
              <span className="text-white font-semibold">
                Human Intelligence
              </span>{" "}
              — the future of collaborative problem-solving
            </p>
          </motion.div>

          {/* Three Core Pillars */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Autonomous Multi-Agent Collaboration */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.1 }}
            >
              <motion.div
                className="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 to-indigo-700 p-10 h-full min-h-[400px] flex flex-col text-white shadow-2xl"
                whileHover={{ y: -10, scale: 1.02 }}
                transition={{ duration: 0.3 }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
                <div className="relative z-10 flex flex-col h-full">
                  <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mb-8 mx-auto">
                    <Brain className="w-10 h-10 text-blue-200" />
                  </div>
                  <h3 className="text-2xl font-bold mb-6 text-center">
                    Autonomous Multi-Agent Collaboration
                  </h3>
                  <p className="text-blue-100 leading-relaxed text-center flex-grow">
                    AI agents work together seamlessly, making intelligent
                    decisions, coordinating tasks, and solving complex problems
                    without constant supervision. Let your agents handle the
                    heavy lifting while you focus on strategy.
                  </p>
                  <div className="mt-8 flex justify-center">
                    <div className="px-4 py-2 bg-white/20 rounded-full text-sm font-medium">
                      🤖 Fully Autonomous
                    </div>
                  </div>
                </div>
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-white/5 rounded-full" />
              </motion.div>
            </motion.div>

            {/* Human in the Loop */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <motion.div
                className="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-purple-600 to-pink-600 p-10 h-full min-h-[400px] flex flex-col text-white shadow-2xl"
                whileHover={{ y: -10, scale: 1.02 }}
                transition={{ duration: 0.3 }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
                <div className="relative z-10 flex flex-col h-full">
                  <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mb-8 mx-auto">
                    <Users className="w-10 h-10 text-purple-200" />
                  </div>
                  <h3 className="text-2xl font-bold mb-6 text-center">
                    Human in the Loop
                  </h3>
                  <p className="text-purple-100 leading-relaxed text-center flex-grow">
                    Maintain control when it matters. Step in for critical
                    decisions, provide guidance, approve sensitive actions, and
                    ensure AI agents align with your values and business
                    objectives. The perfect blend of automation and human
                    oversight.
                  </p>
                  <div className="mt-8 flex justify-center">
                    <div className="px-4 py-2 bg-white/20 rounded-full text-sm font-medium">
                      👥 Human Oversight
                    </div>
                  </div>
                </div>
                <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-white/5 rounded-full" />
              </motion.div>
            </motion.div>

            {/* DeepSeek First */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.3 }}
            >
              <motion.div
                className="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-600 to-teal-600 p-10 h-full min-h-[400px] flex flex-col text-white shadow-2xl"
                whileHover={{ y: -10, scale: 1.02 }}
                transition={{ duration: 0.3 }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
                <div className="relative z-10 flex flex-col h-full">
                  <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mb-8 mx-auto">
                    <Zap className="w-10 h-10 text-emerald-200" />
                  </div>
                  <h3 className="text-2xl font-bold mb-6 text-center">
                    Cost in Mind
                  </h3>
                  <p className="text-emerald-100 leading-relaxed text-center flex-grow">
                    Optimized for low-cost LLM models like DeepSeek, Claude
                    Haiku, and Gemini Flash. Get enterprise-grade performance
                    without breaking the bank. Smart token management and
                    efficient prompt engineering reduce costs by up to 90%
                    compared to premium models.
                  </p>
                  <div className="mt-8 flex justify-center">
                    <div className="px-4 py-2 bg-white/20 rounded-full text-sm font-medium">
                      💰 Cost Optimized
                    </div>
                  </div>
                </div>
                <div className="absolute -top-10 -left-10 w-24 h-24 bg-white/5 rounded-full" />
                <div className="absolute -bottom-10 -right-10 w-24 h-24 bg-white/5 rounded-full" />
              </motion.div>
            </motion.div>
          </div>

          {/* Bottom CTA */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="text-center mt-16"
          >
            <p className="text-lg text-purple-200 mb-8">
              Ready to experience the future of AI collaboration?
            </p>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="/architecture"
                className="inline-flex items-center bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white font-semibold px-8 py-4 rounded-xl transition-all duration-300 shadow-lg"
              >
                <Sparkles className="mr-3 h-5 w-5" />
                Explore the Architecture
                <ArrowRight className="ml-3 h-5 w-5" />
              </Link>
            </motion.div>
          </motion.div>
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
              Ready to Get Started?
            </h2>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Join developers building the next generation of AI-powered
              applications
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
