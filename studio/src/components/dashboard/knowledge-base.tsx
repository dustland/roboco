"use client";

import { useState } from "react";
import { Database, Book, Star, Coffee } from "lucide-react";
import { Button } from "../ui/button";

interface KnowledgeItem {
  id: string;
  category: string;
  title: string;
  description: string;
  confidence: number;
  icon: React.ElementType;
}

const initialKnowledge: KnowledgeItem[] = [
  {
    id: "1",
    category: "Task Knowledge",
    title: "Coffee Preparation",
    description: "Understanding different coffee types and preparation methods",
    confidence: 0.95,
    icon: Coffee,
  },
  {
    id: "2",
    category: "User Preferences",
    title: "Individual Preferences",
    description: "Learned preferences for different users",
    confidence: 0.85,
    icon: Star,
  },
  {
    id: "3",
    category: "General Knowledge",
    title: "Common Interactions",
    description: "Basic conversation and interaction patterns",
    confidence: 0.9,
    icon: Book,
  },
];

export function KnowledgeBase() {
  const [knowledge] = useState<KnowledgeItem[]>(initialKnowledge);

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Knowledge Base</h2>
          <Database className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="space-y-4">
          {knowledge.map((item) => (
            <div key={item.id} className="p-4 rounded-md bg-muted/50 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-full bg-primary/10">
                    <item.icon className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{item.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {item.category}
                    </p>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {(item.confidence * 100).toFixed(0)}% confidence
                </div>
              </div>
              <p className="text-sm">{item.description}</p>
              <div className="w-full bg-secondary/30 rounded-full h-1.5">
                <div
                  className="bg-primary h-1.5 rounded-full"
                  style={{ width: `${item.confidence * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
