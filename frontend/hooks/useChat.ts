import { useState, useCallback, useRef } from 'react';
import { useMutation, useQuery, gql } from '@apollo/client';

// ── GraphQL operations ────────────────────────────────────────────────────────

const CREATE_SESSION = gql`
  mutation CreateChatSession($userId: Int) {
    createChatSession(userId: $userId) {
      id title createdAt updatedAt messages { id role content metadata createdAt }
    }
  }
`;

const SEND_MESSAGE = gql`
  mutation SendMessage($sessionId: String!, $message: String!, $useLlm: Boolean, $useCrew: Boolean) {
    sendMessage(sessionId: $sessionId, message: $message, useLlm: $useLlm, useCrew: $useCrew) {
      id sessionId role content metadata createdAt
    }
  }
`;

const GET_HISTORY = gql`
  query GetChatHistory($sessionId: String!) {
    getChatHistory(sessionId: $sessionId) {
      id sessionId role content metadata createdAt
    }
  }
`;

const GET_SESSIONS = gql`
  query GetChatSessions($userId: Int) {
    getChatSessions(userId: $userId) {
      id title createdAt updatedAt
      messages { id role content createdAt }
    }
  }
`;

const CLEAR_SESSION = gql`
  mutation ClearChatSession($sessionId: String!) {
    clearChatSession(sessionId: $sessionId)
  }
`;

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: string | null;
  createdAt: string;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title?: string | null;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
}

export interface ParsedMetadata {
  intent?: string;
  confidence?: number;
  processing_time_ms?: number;
  followup?: boolean;
  agents_skipped?: boolean;
  sources?: Array<{
    content: string;
    relevance_score: number;
    metadata?: { act?: string; section?: string; title?: string };
  }>;
  graph_references?: Array<{
    case_name?: string;
    case_year?: number;
    act_name?: string;
    section?: string;
    section_title?: string;
    relationship?: string;
  }>;
  web_sources?: Array<{
    title?: string;
    url?: string;
    content?: string;
    web_source?: string;
  }>;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useChat(userId?: number, token?: string | null) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  const [createSessionMutation] = useMutation(CREATE_SESSION);
  const [sendMessageMutation] = useMutation(SEND_MESSAGE);
  const [clearSessionMutation] = useMutation(CLEAR_SESSION);

  const { data: sessionsData, refetch: refetchSessions } = useQuery(GET_SESSIONS, {
    variables: { userId },
    skip: !userId,
  });

  // ── Start new session ─────────────────────────────────────────────────────

  const startNewSession = useCallback(async () => {
    const { data } = await createSessionMutation({ variables: { userId } });
    const newSession = data?.createChatSession;
    if (newSession) {
      setSessionId(newSession.id);
      setMessages([]);
    }
    return newSession?.id;
  }, [createSessionMutation, userId]);

  // ── Load existing session ─────────────────────────────────────────────────

  const loadSession = useCallback((sid: string, history: Message[]) => {
    setSessionId(sid);
    setMessages(history);
  }, []);

  // ── Send message (standard) ───────────────────────────────────────────────

  const sendMessage = useCallback(async (
    content: string,
    useLlm = true,
    useCrew = false,
  ) => {
    if (!content.trim() || isLoading) return;

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await startNewSession() || null;
      if (!currentSessionId) return;
    }

    // Optimistically add user message
    const userMsg: Message = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    // Add placeholder assistant message
    const placeholderId = `temp-assistant-${Date.now()}`;
    setMessages(prev => [...prev, {
      id: placeholderId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
      isStreaming: true,
    }]);

    try {
      const { data } = await sendMessageMutation({
        variables: { sessionId: currentSessionId, message: content, useLlm, useCrew },
      });

      const assistantMsg = data?.sendMessage;
      if (assistantMsg) {
        setMessages(prev => prev.map(m =>
          m.id === placeholderId ? { ...assistantMsg, isStreaming: false } : m
        ));
      }
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === placeholderId
          ? { ...m, content: 'Sorry, something went wrong. Please try again.', isStreaming: false }
          : m
      ));
    } finally {
      setIsLoading(false);
      refetchSessions();
    }
  }, [sessionId, isLoading, startNewSession, sendMessageMutation, refetchSessions]);

  // ── Send message with streaming ───────────────────────────────────────────

  const sendMessageStream = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = await startNewSession() || null;
      if (!currentSessionId) return;
    }

    const userMsg: Message = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setStreamingContent('');

    const streamingId = `streaming-${Date.now()}`;
    setMessages(prev => [...prev, {
      id: streamingId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
      isStreaming: true,
    }]);

    abortRef.current = new AbortController();

    try {
      // ✅ Use the backend proxy — JWT auth only, no INTERNAL_API_KEY in browser
      const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:4000';
      const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // JWT from auth context (never the internal API key)
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          sessionId: currentSessionId,
          message: content,
          useLlm: true,
        }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? ''; // keep incomplete line

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'session_id' && data.session_id) {
                // Update session if backend created a new one
                if (!sessionId) setSessionId(data.session_id);

              } else if (data.type === 'token') {
                fullContent += data.content;
                setMessages(prev => prev.map(m =>
                  m.id === streamingId ? { ...m, content: fullContent } : m
                ));

              } else if (data.type === 'done') {
                // Attach rich metadata (sources, graph refs) from the done event
                const richMetadata = JSON.stringify({
                  intent: data.intent,
                  confidence: data.confidence,
                  sources: data.sources || [],
                  graph_references: data.graph_references || [],
                  web_sources: data.web_sources || [],
                  streamed: true,
                });
                setMessages(prev => prev.map(m =>
                  m.id === streamingId
                    ? { ...m, isStreaming: false, metadata: richMetadata }
                    : m
                ));

              } else if (data.type === 'error') {
                setMessages(prev => prev.map(m =>
                  m.id === streamingId
                    ? { ...m, content: `Error: ${data.message}`, isStreaming: false }
                    : m
                ));
              }
            } catch { /* skip malformed chunks */ }
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') {
        setMessages(prev => prev.map(m =>
          m.id === streamingId
            ? { ...m, content: 'Stream error. Please try again.', isStreaming: false }
            : m
        ));
      }
    } finally {
      setIsLoading(false);
      setStreamingContent('');
      refetchSessions();
    }
  }, [sessionId, isLoading, startNewSession, refetchSessions, token]);

  // ── Clear session ─────────────────────────────────────────────────────────

  const clearSession = useCallback(async () => {
    if (!sessionId) return;
    await clearSessionMutation({ variables: { sessionId } });
    setSessionId(null);
    setMessages([]);
    refetchSessions();
  }, [sessionId, clearSessionMutation, refetchSessions]);

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    sessionId,
    messages,
    isLoading,
    streamingContent,
    sessions: (sessionsData?.getChatSessions || []) as ChatSession[],
    sendMessage,
    sendMessageStream,
    startNewSession,
    loadSession,
    clearSession,
    stopStreaming,
  };
}

// ── Helper: parse message metadata ───────────────────────────────────────────

export function parseMetadata(metadata?: string | null): ParsedMetadata {
  if (!metadata) return {};
  try {
    return JSON.parse(metadata) as ParsedMetadata;
  } catch {
    return {};
  }
}
