'use client';

import { useState, useEffect, FormEvent, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { useQuery } from '@apollo/client';
import { SEARCH_QUERY } from '@/lib/graphql/queries';
import SearchResults from '@/components/SearchResults';
import Header from '@/components/Header';
import SearchHistory, { addToSearchHistory } from '@/components/SearchHistory';
import { SearchResultsSkeleton } from '@/components/LoadingSpinner';
import QuickActionsMenu from '@/components/QuickActionsMenu';
import TopLoadingBar from '@/components/TopLoadingBar';
import OnboardingTutorial from '@/components/OnboardingTutorial';
import IllustratedEmptyState from '@/components/IllustratedEmptyState';

export default function SearchPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, user, logout } = useAuth();
  const { showToast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [queryText, setQueryText] = useState('');
  const [useLlm, setUseLlm] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K to focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search')?.focus();
      }
      // Ctrl/Cmd + / to show keyboard shortcuts
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        // Trigger FAB menu to show shortcuts
        const fabButton = document.querySelector('[aria-label="Quick actions menu"]') as HTMLElement;
        fabButton?.click();
      }
      // Escape to clear search
      if (e.key === 'Escape') {
        setQueryText('');
        document.getElementById('search')?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Scroll to top button visibility
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSearch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    const query = queryText.trim();
    setSearchQuery(query);
    setHasSearched(true);

    // Add to search history
    addToSearchHistory(query, useLlm);

    // Refetch with new query
    try {
      await refetch({ query, useLlm });
    } catch (err) {
      console.error('Search error:', err);
      showToast('Search failed. Please try again.', 'error');
    }
  };

  const handleHistorySelect = useCallback((query: string, llm: boolean) => {
    setQueryText(query);
    setUseLlm(llm);
    setSearchQuery(query);
    setHasSearched(true);

    refetch({ query, useLlm: llm }).catch((err) => {
      console.error('Search error:', err);
      showToast('Search failed. Please try again.', 'error');
    });
  }, [refetch, showToast]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900 transition-colors">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors duration-300">
      <Header user={user} onLogout={logout} />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search History */}
        <SearchHistory onSelectQuery={handleHistorySelect} />

        {/* Search Form */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-soft p-6 mb-6 transform transition-all duration-300 hover:shadow-elevation-2 animate-fade-in">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Ask a Legal Question
                <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">(Press Ctrl+K to focus)</span>
              </label>
              <div className="flex gap-4">
                <input
                  id="search"
                  type="text"
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="e.g., What is the punishment for murder in IPC?"
                  className="flex-1 px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 bg-white dark:bg-slate-700 transition-all duration-300"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !queryText.trim()}
                  className="px-6 py-3 bg-gradient-primary text-white rounded-lg hover:shadow-elevation-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium transform hover:-translate-y-0.5 active:translate-y-0"
                >
                  {loading ? (
                    <span className="flex items-center space-x-2">
                      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Searching...</span>
                    </span>
                  ) : (
                    'Search'
                  )}
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <input
                id="use-llm"
                type="checkbox"
                checked={useLlm}
                onChange={(e) => setUseLlm(e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-slate-600 rounded transition-colors"
              />
              <label htmlFor="use-llm" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                Use LLM for answer generation (slower but more conversational)
              </label>
            </div>
          </form>
        </div>

        {/* Loading State */}
        {loading && <SearchResultsSkeleton />}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900 dark:bg-opacity-20 border border-red-200 dark:border-red-800 rounded-lg p-6 mb-6 animate-slide-up">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Error searching legal documents
                </h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  <p>{error.message || 'An error occurred while processing your query. Please try again.'}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setQueryText('');
                      setHasSearched(false);
                    }}
                    className="text-sm font-medium text-red-800 dark:text-red-200 hover:text-red-900 dark:hover:text-red-100 underline transition-colors"
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
          <div className="animate-fade-in">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Results for: &quot;{data.search.question}&quot;
              </h2>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {data.search.processing_time_ms && (
                  <span>{(data.search.processing_time_ms / 1000).toFixed(2)}s</span>
                )}
              </div>
            </div>
            <SearchResults result={data.search} />
          </div>
        )}

        {/* Empty State - No Results */}
        {!loading && !error && !data?.search && hasSearched && (
          <IllustratedEmptyState type="no-results" />
        )}

        {/* Initial State - Before First Search */}
        {!loading && !error && !data?.search && !hasSearched && (
          <IllustratedEmptyState type="search" />
        )}
      </main>

      {/* Quick Actions FAB */}
      <QuickActionsMenu />

      {/* Top Loading Bar */}
      <TopLoadingBar />

      {/* Onboarding Tutorial */}
      {showOnboarding && (
        <OnboardingTutorial onComplete={() => setShowOnboarding(false)} />
      )}
    </div>
  );
}
