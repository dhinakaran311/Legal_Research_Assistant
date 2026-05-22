'use client';

import { useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import ChatWindow from '@/components/chat/ChatWindow';
import ChatInput from '@/components/chat/ChatInput';
import SessionSidebar from '@/components/chat/SessionSidebar';
import Header from '@/components/Header';
import { useChat, ChatSession } from '@/hooks/useChat';

export default function ChatPage() {
  const router = useRouter();
  const { user, token, loading: authLoading, isAuthenticated, logout } = useAuth();

  // ── Auth guard ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  const {
    sessionId, messages, isLoading, sessions,
    sendMessage, sendMessageStream,
    startNewSession, loadSession, clearSession, stopStreaming,
  } = useChat(user?.id, token);

  const handleSelectSession = useCallback(async (session: ChatSession) => {
    loadSession(session.id, session.messages || []);
  }, [loadSession]);

  const handleNewChat = useCallback(async () => {
    await startNewSession();
  }, [startNewSession]);

  // Handle suggestion chip clicks — sends the suggestion text as a stream
  const handleSuggestion = useCallback((text: string) => {
    sendMessageStream(text);
  }, [sendMessageStream]);

  // Show loading spinner until auth resolves
  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <div className="flex flex-col items-center gap-3">
          <span className="text-3xl animate-pulse">⚖️</span>
          <p className="text-gray-400 text-sm">Loading…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100">
      {/* Shared navigation header — theme toggle, user menu, search link */}
      <Header user={user} onLogout={logout} />

      {/* Chat workspace */}
      <div className="flex flex-1 min-h-0">
        {/* Session sidebar */}
        <SessionSidebar
          sessions={sessions}
          currentSessionId={sessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onClearSession={clearSession}
        />

        {/* Main chat area */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* Session info bar */}
          <div className="flex items-center justify-between px-6 py-2 border-b border-gray-800 bg-gray-900/50 text-xs text-gray-500">
            <span>
              {sessionId
                ? `Session: ${sessionId.slice(0, 8)}…`
                : 'No active session — start a conversation below'}
            </span>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span>AI Engine connected</span>
            </div>
          </div>

          {/* Messages */}
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            onSuggestionClick={handleSuggestion}
          />

          {/* Input */}
          <ChatInput
            onSend={(msg) => sendMessage(msg, true, false)}
            onStream={sendMessageStream}
            isLoading={isLoading}
            onStop={stopStreaming}
          />
        </div>
      </div>
    </div>
  );
}
