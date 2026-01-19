'use client';

import React, { useEffect, useState, useCallback } from 'react';

interface SearchHistoryItem {
    query: string;
    timestamp: number;
    useLlm: boolean;
}

interface SearchHistoryProps {
    onSelectQuery: (query: string, useLlm: boolean) => void;
    userId?: string; // User ID to make history user-specific
}

export default function SearchHistory({ onSelectQuery, userId }: SearchHistoryProps) {
    const [history, setHistory] = useState<SearchHistoryItem[]>([]);
    const [isExpanded, setIsExpanded] = useState(false);

    // Create user-specific storage key
    const getStorageKey = useCallback(() => {
        return userId ? `searchHistory_${userId}` : 'searchHistory';
    }, [userId]);

    const loadHistory = useCallback(() => {
        try {
            const saved = localStorage.getItem(getStorageKey());
            if (saved) {
                setHistory(JSON.parse(saved));
            } else {
                setHistory([]);
            }
        } catch (error) {
            console.error('Failed to load search history:', error);
        }
    }, [getStorageKey]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]); // Now properly includes all dependencies

    const clearHistory = () => {
        localStorage.removeItem(getStorageKey());
        setHistory([]);
    };

    const clearItem = (index: number) => {
        const newHistory = history.filter((_, i) => i !== index);
        localStorage.setItem(getStorageKey(), JSON.stringify(newHistory));
        setHistory(newHistory);
    };

    const formatTimestamp = (timestamp: number) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    };

    if (history.length === 0) {
        return null;
    }

    return (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-4 mb-6 transition-all duration-300 hover:shadow-md">
            <div className="flex items-center justify-between mb-3">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center space-x-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                    <svg
                        className={`h-5 w-5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="font-medium">Recent Searches ({history.length})</span>
                </button>
                {isExpanded && (
                    <button
                        onClick={clearHistory}
                        className="text-xs text-red-600 dark:text-red-400 hover:underline transition-colors"
                    >
                        Clear All
                    </button>
                )}
            </div>

            {isExpanded && (
                <div className="space-y-2 animate-slide-up">
                    {history.slice(0, 10).map((item, index) => (
                        <div
                            key={index}
                            className="group flex items-center justify-between p-2 rounded-md hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors cursor-pointer"
                        >
                            <button
                                onClick={() => onSelectQuery(item.query, item.useLlm)}
                                className="flex-1 text-left"
                            >
                                <p className="text-sm text-gray-700 dark:text-gray-300 truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                    {item.query}
                                </p>
                                <div className="flex items-center space-x-2 mt-1">
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
                                        {formatTimestamp(item.timestamp)}
                                    </span>
                                    {item.useLlm && (
                                        <span className="text-xs px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded">
                                            LLM
                                        </span>
                                    )}
                                </div>
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    clearItem(index);
                                }}
                                className="opacity-0 group-hover:opacity-100 transition-opacity ml-2 p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400"
                            >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export function addToSearchHistory(query: string, useLlm: boolean, userId?: string) {
    try {
        // Create user-specific storage key
        const storageKey = userId ? `searchHistory_${userId}` : 'searchHistory';

        const saved = localStorage.getItem(storageKey);
        const history: SearchHistoryItem[] = saved ? JSON.parse(saved) : [];

        // Don't add duplicate consecutive queries
        if (history.length > 0 && history[0].query === query) {
            return;
        }

        const newItem: SearchHistoryItem = {
            query,
            timestamp: Date.now(),
            useLlm,
        };

        const newHistory = [newItem, ...history.filter(item => item.query !== query)].slice(0, 10);
        localStorage.setItem(storageKey, JSON.stringify(newHistory));
    } catch (error) {
        console.error('Failed to save search history:', error);
    }
}
