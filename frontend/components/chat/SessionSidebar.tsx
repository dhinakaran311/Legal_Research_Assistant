'use client';

import { ChatSession } from '@/hooks/useChat';

interface Props {
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (session: ChatSession) => void;
  onNewChat: () => void;
  onClearSession: () => void;
}

export default function SessionSidebar({
  sessions, currentSessionId, onSelectSession, onNewChat, onClearSession,
}: Props) {
  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-blue-600
            hover:bg-blue-700 text-white text-sm font-medium transition-colors">
          <span className="text-lg leading-none">+</span>
          New Chat
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.length === 0 ? (
          <p className="text-xs text-gray-600 text-center mt-4 px-2">
            No previous chats
          </p>
        ) : (
          sessions.map(session => (
            <button
              key={session.id}
              onClick={() => onSelectSession(session)}
              className={`w-full text-left px-3 py-2 rounded-xl text-sm transition-colors group ${
                session.id === currentSessionId
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}>
              <p className="truncate font-medium">
                {session.title || 'New conversation'}
              </p>
              <p className="text-xs text-gray-600 mt-0.5">
                {new Date(session.updatedAt).toLocaleDateString()}
              </p>
            </button>
          ))
        )}
      </div>

      {/* Footer */}
      {currentSessionId && (
        <div className="p-3 border-t border-gray-700">
          <button
            onClick={onClearSession}
            className="w-full text-xs text-gray-500 hover:text-red-400 transition-colors py-1">
            Clear current chat
          </button>
        </div>
      )}
    </aside>
  );
}
