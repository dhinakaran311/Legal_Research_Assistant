'use client';

import React from 'react';

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
  return (
    <div className="space-y-6">
      {/* Answer Section */}
      <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-primary-600">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Answer
            </h2>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>
                Intent: <span className="font-medium text-gray-700">{result.intent}</span>
              </span>
              <span>
                Confidence: <span className="font-medium text-gray-700">{(result.confidence * 100).toFixed(1)}%</span>
              </span>
              <span>
                Processed in: <span className="font-medium text-gray-700">{result.processing_time_ms.toFixed(0)}ms</span>
              </span>
            </div>
          </div>
        </div>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
            {result.answer}
          </p>
        </div>
      </div>

      {/* Sources Section */}
      {result.sources && result.sources.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Sources ({result.sources.length})
          </h3>
          <div className="space-y-4">
            {result.sources.map((source, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    {source.metadata.act && (
                      <span className="inline-block px-2 py-1 text-xs font-medium bg-primary-100 text-primary-800 rounded mr-2">
                        {source.metadata.act}
                      </span>
                    )}
                    {source.metadata.section && (
                      <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded mr-2">
                        Section {source.metadata.section}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-medium text-gray-500">
                    {(source.relevance_score * 100).toFixed(1)}% relevant
                  </span>
                </div>
                <p className="text-sm text-gray-700 line-clamp-3">
                  {source.content}
                </p>
                {source.metadata.title && (
                  <p className="text-xs text-gray-500 mt-2">
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
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Related Cases & Sections ({result.graph_references.length})
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {result.graph_references.map((ref, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 transition-colors"
              >
                {ref.case_name && (
                  <div className="mb-2">
                    <h4 className="font-medium text-gray-900">
                      {ref.case_name}
                      {ref.case_year && (
                        <span className="text-gray-500"> ({ref.case_year})</span>
                      )}
                    </h4>
                  </div>
                )}
                {ref.section && ref.act_name && (
                  <div className="text-sm text-gray-600 mb-2">
                    <span className="font-medium">{ref.act_name}</span>
                    {ref.section && (
                      <>
                        {' '}· Section{' '}
                        <span className="font-medium">{ref.section}</span>
                      </>
                    )}
                    {ref.section_title && (
                      <div className="text-xs text-gray-500 mt-1">
                        {ref.section_title}
                      </div>
                    )}
                  </div>
                )}
                {ref.relationship && (
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                    {ref.relationship}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Documents Used:</span>
            <span className="ml-2 font-medium text-gray-900">{result.documents_used}</span>
          </div>
          <div>
            <span className="text-gray-500">Intent Confidence:</span>
            <span className="ml-2 font-medium text-gray-900">{(result.intent_confidence * 100).toFixed(1)}%</span>
          </div>
          <div>
            <span className="text-gray-500">Retrieved:</span>
            <span className="ml-2 font-medium text-gray-900">
              {result.retrieval_strategy.num_documents_returned} / {result.retrieval_strategy.num_documents_requested}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Threshold:</span>
            <span className="ml-2 font-medium text-gray-900">
              {(result.retrieval_strategy.min_relevance_threshold * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        {result.retrieval_strategy.intent_reasoning && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <span className="text-xs text-gray-500">Reasoning: </span>
            <span className="text-xs text-gray-700">{result.retrieval_strategy.intent_reasoning}</span>
          </div>
        )}
      </div>
    </div>
  );
}
