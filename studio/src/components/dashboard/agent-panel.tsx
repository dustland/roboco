"use client";

import { useState } from "react";
import {
  Brain,
  MessageSquare,
  Database,
  ChartBar,
  Sparkles,
} from "lucide-react";
import { Button } from "../ui/button";

interface Agent {
  id: string;
  name: string;
  role: string;
  status: "active" | "inactive";
  icon: React.ElementType;
}

const initialAgents: Agent[] = [
  {
    id: "1",
    name: "Interaction Manager",
    role: "Handles user requests and coordinates responses",
    status: "active",
    icon: MessageSquare,
  },
  {
    id: "2",
    name: "Behavior Planner",
    role: "Plans and coordinates robot actions",
    status: "active",
    icon: Brain,
  },
  {
    id: "3",
    name: "Knowledge Engineer",
    role: "Maintains and updates knowledge base",
    status: "active",
    icon: Database,
  },
  {
    id: "4",
    name: "Performance Analyst",
    role: "Monitors and analyzes system performance",
    status: "active",
    icon: ChartBar,
  },
  {
    id: "5",
    name: "Learning Coordinator",
    role: "Implements improvements and updates",
    status: "active",
    icon: Sparkles,
  },
];

export function AgentPanel() {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);

  const toggleAgentStatus = (agentId: string) => {
    setAgents(
      agents.map((agent) =>
        agent.id === agentId
          ? {
              ...agent,
              status: agent.status === "active" ? "inactive" : "active",
            }
          : agent
      )
    );
  };

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6 space-y-4">
        <h2 className="text-2xl font-bold">Agent Team</h2>
        <div className="space-y-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="flex items-center justify-between p-4 rounded-md bg-muted/50"
            >
              <div className="flex items-center space-x-4">
                <div className="p-2 rounded-full bg-primary/10">
                  <agent.icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">{agent.name}</h3>
                  <p className="text-sm text-muted-foreground">{agent.role}</p>
                </div>
              </div>
              <Button
                variant={agent.status === "active" ? "default" : "outline"}
                size="sm"
                onClick={() => toggleAgentStatus(agent.id)}
              >
                {agent.status === "active" ? "Active" : "Inactive"}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
