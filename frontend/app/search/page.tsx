'use client';

import { useState, useEffect, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery } from '@apollo/client';
import { SEARCH_QUERY } from '@/lib/graphql/queries';
import SearchResults from '@/components/SearchResults';

export default function SearchPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [queryText, setQueryText] = useState('');
  const [useLlm, setUseLlm] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const { data, loading, error, refetch } = useQuery(SEARCH_QUERY, {
    variables: { query: searchQuery, useLlm },
    skip: !searchQuery || !hasSearched,
    errorPolicy: 'all',
    fetchPolicy: 'network-only',
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSearch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!queryText.trim()) return;
    
    const query = queryText.trim();
    setSearchQuery(query);
    setHasSearched(true);
    
    // Refetch with new query
    try {
      await refetch({ query, useLlm });
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Legal Research Assistant
              </h1>
              <p className="text-sm text-gray-500">AI-powered legal research</p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user?.name}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Form */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                Ask a Legal Question
              </label>
              <div className="flex gap-4">
                <input
                  id="search"
                  type="text"
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="e.g., What is the punishment for murder in IPC?"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !queryText.trim()}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>
            <div className="flex items-center">
              <input
                id="use-llm"
                type="checkbox"
                checked={useLlm}
                onChange={(e) => setUseLlm(e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="use-llm" className="ml-2 block text-sm text-gray-700">
                Use LLM for answer generation (slower but more conversational)
              </label>
            </div>
          </form>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Searching legal documents...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error searching legal documents
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error.message || 'An error occurred while processing your query. Please try again.'}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setQueryText('');
                      setHasSearched(false);
                    }}
                    className="text-sm font-medium text-red-800 hover:text-red-900 underline"
                  >
                    Clear and try again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Search Results */}
        {!loading && !error && data?.search && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Results for: &quot;{data.search.question}&quot;
              </h2>
            </div>
            <SearchResults result={data.search} />
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && !data?.search && hasSearched && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No results found</h3>
            <p className="mt-2 text-sm text-gray-500">
              Try rephrasing your question or check if the backend services are running.
            </p>
          </div>
        )}

        {/* Initial State - Before First Search */}
        {!loading && !error && !data?.search && !hasSearched && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">Start your legal research</h3>
            <p className="mt-2 text-sm text-gray-500">
              Enter a legal question above to search through acts, judgments, and legal documents.
            </p>
            <div className="mt-6 text-left max-w-md mx-auto">
              <p className="text-sm font-medium text-gray-700 mb-2">Example queries:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• What is the punishment for murder?</li>
                <li>• How do I file an FIR?</li>
                <li>• What is anticipatory bail?</li>
                <li>• What is the difference between murder and culpable homicide?</li>
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
