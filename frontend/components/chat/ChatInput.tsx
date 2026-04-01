'use client';

import { useState, useRef, KeyboardEvent } from 'react';

interface Props {
  onSend: (message: string) => void;
  onStream?: (message: string) => void;
  isLoading: boolean;
  onStop?: () => void;
  placeholder?: string;
}

export default function ChatInput({ onSend, onStream, isLoading, onStop, placeholder }: Props) {
  const [value, setValue] = useState('');
  const [useStream, setUseStream] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    if (useStream && onStream) {
      onStream(trimmed);
    } else {
      onSend(trimmed);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  return (
    <div className="border-t border-gray-700 bg-gray-900 px-4 py-3">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-2 bg-gray-800 border border-gray-600 rounded-2xl px-4 py-2
          focus-within:border-blue-500 transition-colors">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={e => { setValue(e.target.value); handleInput(); }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || 'Ask a legal question... (Enter to send, Shift+Enter for new line)'}
            rows={1}
            disabled={isLoading}
            className="flex-1 bg-transparent text-gray-100 placeholder-gray-500 text-sm resize-none
              outline-none py-1 max-h-40 disabled:opacity-50"
          />

          <div className="flex items-center gap-2 pb-1">
            {/* Stream toggle */}
            {onStream && (
              <button
                onClick={() => setUseStream(s => !s)}
                title={useStream ? 'Streaming on' : 'Streaming off'}
                className={`text-xs px-2 py-1 rounded-lg transition-colors ${
                  useStream
                    ? 'bg-blue-600/30 text-blue-400 border border-blue-600/50'
                    : 'text-gray-500 hover:text-gray-300'
                }`}>
                ⚡
              </button>
            )}

            {/* Stop / Send */}
            {isLoading ? (
              <button
                onClick={onStop}
                className="w-8 h-8 flex items-center justify-center rounded-xl bg-red-600/20
                  text-red-400 hover:bg-red-600/30 transition-colors">
                ■
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!value.trim()}
                className="w-8 h-8 flex items-center justify-center rounded-xl bg-blue-600
                  text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed
                  transition-colors">
                ↑
              </button>
            )}
          </div>
        </div>

        <p className="text-xs text-gray-600 mt-1 text-center">
          AI legal research assistant · Not legal advice
        </p>
      </div>
    </div>
  );
}
