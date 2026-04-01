'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Message, parseMetadata } from '@/hooks/useChat';

interface Props {
  message: Message;
}

// ── Confidence badge (reused from SearchResults) ──────────────────────────────
function ConfidenceBadge({ confidence }: { confidence: number }) {
  if (confidence >= 0.8)
    return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">High Confidence</span>;
  if (confidence >= 0.5)
    return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">Medium Confidence</span>;
  return <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">Low Confidence</span>;
}

// ── Typing dots ───────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-1 items-center py-1 px-1">
      {[0, 150, 300].map(delay => (
        <span key={delay} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
          style={{ animationDelay: `${delay}ms` }} />
      ))}
    </div>
  );
}

// ── User bubble ───────────────────────────────────────────────────────────────
function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end mb-4">
      <div className="flex items-end gap-2">
        <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
          U
        </div>
      </div>
    </div>
  );
}

// ── Assistant rich bubble ─────────────────────────────────────────────────────
function AssistantBubble({ message }: { message: Message }) {
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [copied, setCopied] = useState(false);
  const meta = parseMetadata(message.metadata);
  const isFollowup = meta.followup === true;

  const toggleSource = (i: number) => {
    setExpandedSources(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  const copyAnswer = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Loading state
  if (message.isStreaming && !message.content) {
    return (
      <div className="flex justify-start mb-4">
        <div className="flex items-end gap-2">
          <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-200 flex-shrink-0">⚖️</div>
          <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-bl-sm px-4 py-3">
            <TypingDots />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2 w-full max-w-[90%]">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs flex-shrink-0 mt-1">⚖️</div>

        <div className="flex-1 space-y-3">

          {/* ── Answer card ── */}
          <div className="bg-gray-800 border-l-4 border-blue-500 border border-gray-700 rounded-2xl rounded-tl-sm p-4">
            {/* Header row */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex flex-wrap items-center gap-2">
                {meta.confidence !== undefined && <ConfidenceBadge confidence={meta.confidence} />}
                {meta.intent && (
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                    Intent: <span className="text-gray-300 font-medium">{meta.intent}</span>
                  </span>
                )}
                {meta.processing_time_ms !== undefined && (
                  <span className="text-xs text-gray-500">{Math.round(meta.processing_time_ms)}ms</span>
                )}
                {meta.sources && (
                  <span className="text-xs text-gray-500">{meta.sources.length} docs</span>
                )}
              </div>
              <button onClick={copyAnswer}
                className="p-1.5 text-gray-500 hover:text-blue-400 transition-colors rounded-lg hover:bg-gray-700"
                title="Copy answer">
                {copied
                  ? <svg className="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  : <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                }
              </button>
            </div>

            {/* Answer text */}
            <div className="prose prose-invert prose-sm max-w-none text-gray-100">
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}
                components={{
                  a: ({ ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline" />,
                }}>
                {message.content}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-0.5 h-4 bg-blue-400 animate-pulse ml-0.5 align-middle" />
              )}
            </div>
          </div>

          {/* ── Sources — only show for full research answers ── */}
          {!isFollowup && meta.sources && meta.sources.length > 0 && (
            <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                Sources ({meta.sources.length})
              </h4>
              <div className="space-y-3">
                {meta.sources.map((src, i) => (
                  <div key={i} className="border border-gray-700 rounded-lg p-3 hover:border-blue-600/50 transition-colors group">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex flex-wrap gap-1.5">
                        {src.metadata?.act && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-blue-900/50 text-blue-300 rounded-full border border-blue-700/50">
                            {src.metadata.act}
                          </span>
                        )}
                        {src.metadata?.section && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-gray-700 text-gray-300 rounded-full">
                            Section {src.metadata.section}
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-medium px-2 py-0.5 bg-green-900/40 text-green-400 rounded border border-green-700/40 ml-2 flex-shrink-0">
                        {(src.relevance_score * 100).toFixed(1)}% relevant
                      </span>
                    </div>
                    <p className={`text-xs text-gray-400 leading-relaxed ${!expandedSources.has(i) ? 'line-clamp-3' : ''}`}>
                      {src.content}
                    </p>
                    {src.content?.length > 200 && (
                      <button onClick={() => toggleSource(i)}
                        className="mt-1.5 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
                        {expandedSources.has(i) ? 'Show less ↑' : 'Read more ↓'}
                      </button>
                    )}
                    {src.metadata?.title && (
                      <p className="text-xs text-gray-600 mt-1.5 italic">{src.metadata.title}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Graph references — only for full research ── */}
          {!isFollowup && meta.graph_references && meta.graph_references.length > 0 && (
            <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Related Cases & Sections ({meta.graph_references.length})
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {meta.graph_references.map((ref, i) => (
                  <div key={i} className="border border-gray-700 rounded-lg p-3 hover:border-blue-600/50 transition-colors">
                    {ref.case_name && (
                      <p className="text-xs font-medium text-gray-200">
                        {ref.case_name}
                        {ref.case_year && <span className="text-gray-500"> ({ref.case_year})</span>}
                      </p>
                    )}
                    {ref.act_name && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        {ref.act_name}{ref.section ? ` · s.${ref.section}` : ''}
                      </p>
                    )}
                    {ref.relationship && (
                      <span className="mt-1 inline-block px-1.5 py-0.5 text-xs bg-blue-900/40 text-blue-400 rounded border border-blue-700/40">
                        {ref.relationship}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Web sources — only for full research ── */}
          {!isFollowup && meta.web_sources && meta.web_sources.length > 0 && (
            <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <svg className="h-4 w-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                Web Research Results ({meta.web_sources.length})
              </h4>
              <div className="space-y-2">
                {meta.web_sources.map((ws, i) => (
                  <div key={i} className="border border-gray-700 rounded-lg p-3 hover:border-blue-600/50 transition-colors">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-xs font-medium text-gray-200 line-clamp-1">
                        {ws.title || 'Untitled'}
                      </p>
                      {ws.web_source && (
                        <span className="px-1.5 py-0.5 text-xs font-semibold bg-blue-900/40 text-blue-400 rounded border border-blue-700/40 flex-shrink-0">
                          {ws.web_source}
                        </span>
                      )}
                    </div>
                    {ws.content && (
                      <p className="text-xs text-gray-500 line-clamp-2 mb-1.5">{ws.content}</p>
                    )}
                    {ws.url && (
                      <a href={ws.url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors">
                        View Source
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Metadata bar ── */}
          {meta.intent && !message.isStreaming && (
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl px-4 py-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                {meta.sources && (
                  <div>
                    <p className="text-gray-500 mb-0.5">Documents Used</p>
                    <p className="font-semibold text-gray-300">{meta.sources.length}</p>
                  </div>
                )}
                {meta.confidence !== undefined && (
                  <div>
                    <p className="text-gray-500 mb-0.5">Confidence</p>
                    <p className="font-semibold text-gray-300">{(meta.confidence * 100).toFixed(1)}%</p>
                  </div>
                )}
                {meta.processing_time_ms !== undefined && (
                  <div>
                    <p className="text-gray-500 mb-0.5">Response Time</p>
                    <p className="font-semibold text-gray-300">{Math.round(meta.processing_time_ms)}ms</p>
                  </div>
                )}
                {meta.intent && (
                  <div>
                    <p className="text-gray-500 mb-0.5">Intent</p>
                    <p className="font-semibold text-gray-300 capitalize">{meta.intent}</p>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────
export default function MessageBubble({ message }: Props) {
  if (message.role === 'user') return <UserBubble content={message.content} />;
  return <AssistantBubble message={message} />;
}
