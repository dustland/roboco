'use client';

import { useState } from 'react';
import { MessageCircle, User, Bot } from 'lucide-react';

interface Interaction {
  id: string;
  timestamp: Date;
  type: 'user' | 'robot';
  message: string;
  status: 'success' | 'error' | 'pending';
}

const mockInteractions: Interaction[] = [
  {
    id: '1',
    timestamp: new Date(),
    type: 'user',
    message: 'Can you bring me a cup of coffee?',
    status: 'success',
  },
  {
    id: '2',
    timestamp: new Date(),
    type: 'robot',
    message: 'I'll head to the kitchen and prepare your coffee. Do you have any preferences for how you'd like it?',
    status: 'success',
  },
  {
    id: '3',
    timestamp: new Date(),
    type: 'user',
    message: 'Black coffee, no sugar please.',
    status: 'success',
  },
  {
    id: '4',
    timestamp: new Date(),
    type: 'robot',
    message: 'I'll prepare a black coffee without sugar. I'll be back shortly.',
    status: 'pending',
  },
];

export function InteractionLog() {
  const [interactions] = useState<Interaction[]>(mockInteractions);

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Interaction Log</h2>
          <MessageCircle className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="space-y-4">
          {interactions.map((interaction) => (
            <div
              key={interaction.id}
              className={`flex items-start space-x-4 ${
                interaction.type === 'user' ? 'flex-row' : 'flex-row-reverse space-x-reverse'
              }`}
            >
              <div className={`p-2 rounded-full ${
                interaction.type === 'user' ? 'bg-primary/10' : 'bg-secondary/10'
              }`}>
                {interaction.type === 'user' ? (
                  <User className="h-5 w-5 text-primary" />
                ) : (
                  <Bot className="h-5 w-5 text-secondary" />
                )}
              </div>
              <div className={`flex-1 space-y-1 ${
                interaction.type === 'user' ? 'text-left' : 'text-right'
              }`}>
                <p className="text-sm text-muted-foreground">
                  {interaction.timestamp.toLocaleTimeString()}
                </p>
                <div className={`inline-block rounded-lg p-3 ${
                  interaction.type === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground'
                }`}>
                  {interaction.message}
                </div>
                {interaction.status === 'pending' && (
                  <p className="text-xs text-muted-foreground">Processing...</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 