'use client';

import React, { useState } from 'react';
import { useToast } from '@/contexts/ToastContext';

interface SourceMetadata {
  section?: string;
  act?: string;
  chapter?: string;
  title?: string;
}

interface Source {
  content: string;
  relevance_score: number;
  metadata: SourceMetadata;
}

interface GraphReference {
  case_name?: string;
  case_year?: number;
  section?: string;
  section_title?: string;
  act_name?: string;
  related_section?: string;
  related_title?: string;
  relationship?: string;
}

interface RetrievalStrategy {
  num_documents_requested: number;
  min_relevance_threshold: number;
  num_documents_returned: number;
  intent_reasoning: string;
}

interface SearchResult {
  question: string;
  intent: string;
  intent_confidence: number;
  answer: string;
  sources: Source[];
  graph_references: GraphReference[];
  documents_used: number;
  retrieval_strategy: RetrievalStrategy;
  confidence: number;
  processing_time_ms: number;
}

interface SearchResultsProps {
  result: SearchResult;
}

export default function SearchResults({ result }: SearchResultsProps) {
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [copiedAnswer, setCopiedAnswer] = useState(false);
  const { showToast } = useToast();

  const toggleSource = (index: number) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSources(newExpanded);
  };

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === 'answer') {
        setCopiedAnswer(true);
        setTimeout(() => setCopiedAnswer(false), 2000);
      }
      showToast(`${type} copied to clipboard!`, 'success');
    } catch (err) {
      showToast('Failed to copy to clipboard', 'error');
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">High Confidence</span>;
    } else if (confidence >= 0.5) {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">Medium Confidence</span>;
    } else {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">Low Confidence</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Answer Section */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-soft p-6 border-l-4 border-primary-600 transition-all duration-300 hover:shadow-elevation-2 animate-slide-up">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-3">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Answer
              </h2>
              {getConfidenceBadge(result.confidence)}
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-500 dark:text-gray-400">
              <span className="flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                Intent: <span className="font-medium text-gray-700 dark:text-gray-300 ml-1">{result.intent}</span>
              </span>
              <span className="flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-gray-700 dark:text-gray-300">{result.processing_time_ms.toFixed(0)}ms</span>
              </span>
              <span className="flex items-center">
                <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="font-medium text-gray-700 dark:text-gray-300">{result.documents_used} docs</span>
              </span>
            </div>
          </div>
          <button
            onClick={() => copyToClipboard(result.answer, 'Answer')}
            className="ml-4 p-2 text-gray-400 dark:text-gray-500 hover:text-primary-600 dark:hover:text-primary-400 transition-all duration-300 hover:scale-110 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700"
            title="Copy answer"
          >
            {copiedAnswer ? (
              <svg className="h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            )}
          </button>
        </div>
        <div className="prose max-w-none dark:prose-invert">
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {result.answer}
          </p>
        </div>
      </div>

      {/* Sources Section */}
      {result.sources && result.sources.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-soft p-6 transition-all duration-300 hover:shadow-elevation-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <svg className="h-5 w-5 mr-2 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Sources ({result.sources.length})
          </h3>
          <div className="space-y-4">
            {result.sources.map((source, index) => (
              <div
                key={index}
                className="border border-gray-200 dark:border-slate-700 rounded-lg p-4 hover:border-primary-300 dark:hover:border-primary-600 transition-all duration-300 hover:shadow-md group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 flex flex-wrap items-center gap-2">
                    {source.metadata.act && (
                      <span className="inline-block px-3 py-1 text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded-full">
                        {source.metadata.act}
                      </span>
                    )}
                    {source.metadata.section && (
                      <span className="inline-block px-3 py-1 text-xs font-medium bg-gray-100 dark:bg-slate-700 text-gray-800 dark:text-gray-200 rounded-full">
                        Section {source.metadata.section}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <span className="text-xs font-medium px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
                      {(source.relevance_score * 100).toFixed(1)}% relevant
                    </span>
                    <button
                      onClick={() => copyToClipboard(source.content, 'Source')}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 text-gray-400 dark:text-gray-500 hover:text-primary-600 dark:hover:text-primary-400"
                      title="Copy source"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
                <p className={`text-sm text-gray-700 dark:text-gray-300 leading-relaxed ${!expandedSources.has(index) ? 'line-clamp-3' : ''}`}>
                  {source.content}
                </p>
                {source.content.length > 200 && (
                  <button
                    onClick={() => toggleSource(index)}
                    className="mt-2 text-xs font-medium text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center transition-colors"
                  >
                    {expandedSources.has(index) ? (
                      <>
                        <span>Show less</span>
                        <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                        </svg>
                      </>
                    ) : (
                      <>
                        <span>Read more</span>
                        <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </>
                    )}
                  </button>
                )}
                {source.metadata.title && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 italic">
                    {source.metadata.title}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Graph References Section */}
      {result.graph_references && result.graph_references.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-soft p-6 transition-all duration-300 hover:shadow-elevation-2 animate-slide-up" style={{ animationDelay: '200ms' }}>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <svg className="h-5 w-5 mr-2 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Related Cases & Sections ({result.graph_references.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {result.graph_references.map((ref, index) => (
              <div
                key={index}
                className="border border-gray-200 dark:border-slate-700 rounded-lg p-4 hover:border-primary-300 dark:hover:border-primary-600 transition-all duration-300 hover:shadow-md transform hover:-translate-y-1"
              >
                {ref.case_name && (
                  <div className="mb-2">
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {ref.case_name}
                      {ref.case_year && (
                        <span className="text-gray-500 dark:text-gray-400"> ({ref.case_year})</span>
                      )}
                    </h4>
                  </div>
                )}
                {ref.section && ref.act_name && (
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <span className="font-medium text-gray-900 dark:text-gray-200">{ref.act_name}</span>
                    {ref.section && (
                      <>
                        {' '}· Section{' '}
                        <span className="font-medium text-gray-900 dark:text-gray-200">{ref.section}</span>
                      </>
                    )}
                    {ref.section_title && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {ref.section_title}
                      </div>
                    )}
                  </div>
                )}
                {ref.relationship && (
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                    {ref.relationship}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata Section */}
      <div className="bg-gradient-secondary dark:bg-slate-800 rounded-lg p-4 animate-slide-up" style={{ animationDelay: '300ms' }}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex flex-col">
            <span className="text-gray-500 dark:text-gray-400 text-xs mb-1">Documents Used</span>
            <span className="font-semibold text-gray-900 dark:text-white">{result.documents_used}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-gray-500 dark:text-gray-400 text-xs mb-1">Intent Confidence</span>
            <span className="font-semibold text-gray-900 dark:text-white">{(result.intent_confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-gray-500 dark:text-gray-400 text-xs mb-1">Retrieved Docs</span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {result.retrieval_strategy.num_documents_returned} / {result.retrieval_strategy.num_documents_requested}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-gray-500 dark:text-gray-400 text-xs mb-1">Threshold</span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {(result.retrieval_strategy.min_relevance_threshold * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        {result.retrieval_strategy.intent_reasoning && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-slate-700">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Reasoning: </span>
            <span className="text-xs text-gray-700 dark:text-gray-300">{result.retrieval_strategy.intent_reasoning}</span>
          </div>
        )}
      </div>
    </div>
  );
}
