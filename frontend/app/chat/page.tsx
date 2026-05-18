'use client';

import { useCallback } from 'react';
import { useQuery, gql } from '@apollo/client';
import ChatWindow from '@/components/chat/ChatWindow';
import ChatInput from '@/components/chat/ChatInput';
import SessionSidebar from '@/components/chat/SessionSidebar';
import { useChat, ChatSession } from '@/hooks/useChat';

const GET_HISTORY = gql`
  query GetChatHistory($sessionId: String!) {
    getChatHistory(sessionId: $sessionId) {
      id sessionId role content metadata createdAt
    }
  }
`;

export default function ChatPage() {
  const {
    sessionId, messages, isLoading, sessions,
    sendMessage, sendMessageStream,
    startNewSession, loadSession, clearSession, stopStreaming,
  } = useChat();

  const handleSelectSession = useCallback(async (session: ChatSession) => {
    loadSession(session.id, session.messages || []);
  }, [loadSession]);

  const handleNewChat = useCallback(async () => {
    await startNewSession();
  }, [startNewSession]);

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      {/* Sidebar */}
      <SessionSidebar
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onClearSession={clearSession}
      />

      {/* Main chat area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-gray-700 bg-gray-900">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚖️</span>
            <div>
              <h1 className="text-sm font-semibold text-gray-200">Legal Research Assistant</h1>
              <p className="text-xs text-gray-500">
                {sessionId ? `Session: ${sessionId.slice(0, 8)}...` : 'No active session'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs text-gray-500">AI Engine connected</span>
          </div>
        </header>

        {/* Messages */}
        <ChatWindow messages={messages} isLoading={isLoading} />

        {/* Input */}
        <ChatInput
          onSend={(msg) => sendMessage(msg, true, false)}
          onStream={sendMessageStream}
          isLoading={isLoading}
          onStop={stopStreaming}
        />
      </div>
    </div>
  );
}
