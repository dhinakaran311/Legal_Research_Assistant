'use client';

import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { Message } from '@/hooks/useChat';

interface Props {
  messages: Message[];
  isLoading: boolean;
  onSuggestionClick?: (text: string) => void;  // ✅ Bug 4 fix
}

const SUGGESTIONS = [
  'What is anticipatory bail under CrPC Section 438?',
  'What is the punishment for murder under IPC Section 302?',
  'How do I file an FIR?',
  'Difference between IPC and CrPC',
  'What are my rights during arrest?',
  'Explain breach of contract under the Contract Act',
];

export default function ChatWindow({ messages, isLoading, onSuggestionClick }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        {/* Hero icon */}
        <div className="w-20 h-20 rounded-2xl bg-blue-600/20 border border-blue-600/30
          flex items-center justify-center text-4xl mb-5 shadow-lg shadow-blue-900/20">
          ⚖️
        </div>
        <h2 className="text-xl font-semibold text-gray-200 mb-2">
          Legal Research Assistant
        </h2>
        <p className="text-gray-500 text-sm mb-8 max-w-sm leading-relaxed">
          Ask me anything about Indian law. I remember our conversation context
          and cite acts &amp; section numbers.
        </p>

        {/* Suggestion chips — now clickable */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-2xl">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              id={`suggestion-${i}`}
              onClick={() => onSuggestionClick?.(s)}
              className="text-left text-sm text-gray-400 bg-gray-800/50 border border-gray-700
                rounded-xl px-4 py-3 hover:bg-blue-900/30 hover:text-blue-300
                hover:border-blue-600/50 transition-all duration-200 group">
              <span className="mr-2 text-blue-500 group-hover:text-blue-400">→</span>
              {s}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-2">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1 items-center">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
