"use client";

import { useState } from "react";
import { BarChart, Clock, Zap, ThumbsUp } from "lucide-react";

interface Metric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: "up" | "down" | "stable";
  icon: React.ElementType;
}

const initialMetrics: Metric[] = [
  {
    id: "1",
    name: "Response Time",
    value: 1.2,
    unit: "seconds",
    trend: "down",
    icon: Clock,
  },
  {
    id: "2",
    name: "Task Success Rate",
    value: 94,
    unit: "%",
    trend: "up",
    icon: ThumbsUp,
  },
  {
    id: "3",
    name: "System Load",
    value: 45,
    unit: "%",
    trend: "stable",
    icon: Zap,
  },
];

export function PerformanceMetrics() {
  const [metrics] = useState<Metric[]>(initialMetrics);

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Performance Metrics</h2>
          <BarChart className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="grid gap-4">
          {metrics.map((metric) => (
            <div key={metric.id} className="p-4 rounded-md bg-muted/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-full bg-primary/10">
                    <metric.icon className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{metric.name}</h3>
                    <p className="text-2xl font-bold">
                      {metric.value}
                      <span className="text-sm font-normal text-muted-foreground ml-1">
                        {metric.unit}
                      </span>
                    </p>
                  </div>
                </div>
                <div
                  className={`text-sm ${
                    metric.trend === "up"
                      ? "text-green-500"
                      : metric.trend === "down"
                      ? "text-red-500"
                      : "text-yellow-500"
                  }`}
                >
                  {metric.trend === "up"
                    ? "↑"
                    : metric.trend === "down"
                    ? "↓"
                    : "→"}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
