'use client';

import React from 'react';

interface IllustratedEmptyStateProps {
    type?: 'search' | 'no-results' | 'error';
    title?: string;
    description?: string;
    actionLabel?: string;
    onAction?: () => void;
}

export default function IllustratedEmptyState({
    type = 'search',
    title,
    description,
    actionLabel,
    onAction,
}: IllustratedEmptyStateProps) {
    const getIllustration = () => {
        switch (type) {
            case 'search':
                return (
                    <svg className="w-64 h-64 mx-auto" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                        {/* Search illustration */}
                        <circle cx="100" cy="100" r="80" fill="#E0F2FE" className="dark:opacity-20" />
                        <circle cx="80" cy="80" r="35" stroke="#0EA5E9" strokeWidth="4" fill="none" />
                        <line x1="106" y1="106" x2="130" y2="130" stroke="#0EA5E9" strokeWidth="4" strokeLinecap="round" />
                        {/* Document icons */}
                        <rect x="55" y="55" width="20" height="25" rx="2" fill="#0284C7" opacity="0.3" />
                        <rect x="60" y="60" width="20" height="25" rx="2" fill="#0EA5E9" />
                        <line x1="63" y1="65" x2="77" y2="65" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                        <line x1="63" y1="70" x2="77" y2="70" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                        <line x1="63" y1="75" x2="70" y2="75" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                );

            case 'no-results':
                return (
                    <svg className="w-64 h-64 mx-auto" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                        {/* Empty box illustration */}
                        <circle cx="100" cy="100" r="80" fill="#FEF3C7" className="dark:opacity-20" />
                        <rect x="70" y="90" width="60" height="50" rx="4" stroke="#F59E0B" strokeWidth="3" fill="none" />
                        <path d="M70 95 L100 75 L130 95" stroke="#F59E0B" strokeWidth="3" fill="none" />
                        <line x1="100" y1="75" x2="100" y2="140" stroke="#F59E0B" strokeWidth="3" />
                        {/* Question mark */}
                        <text x="100" y="120" fontSize="24" fill="#F59E0B" textAnchor="middle" fontWeight="bold">?</text>
                    </svg>
                );

            case 'error':
                return (
                    <svg className="w-64 h-64 mx-auto" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                        {/* Error illustration */}
                        <circle cx="100" cy="100" r="80" fill="#FEE2E2" className="dark:opacity-20" />
                        <circle cx="100" cy="100" r="40" stroke="#EF4444" strokeWidth="4" fill="none" />
                        <line x1="85" y1="85" x2="115" y2="115" stroke="#EF4444" strokeWidth="4" strokeLinecap="round" />
                        <line x1="115" y1="85" x2="85" y2="115" stroke="#EF4444" strokeWidth="4" strokeLinecap="round" />
                    </svg>
                );
        }
    };

    const getDefaultContent = () => {
        switch (type) {
            case 'search':
                return {
                    title: title || 'Start Your Legal Research',
                    description: description || 'Enter a legal question above to search through acts, judgments, and legal documents.',
                };
            case 'no-results':
                return {
                    title: title || 'No Results Found',
                    description: description || 'Try rephrasing your question or check if the backend services are running.',
                };
            case 'error':
                return {
                    title: title || 'Oops! Something Went Wrong',
                    description: description || 'An error occurred while processing your request. Please try again.',
                };
        }
    };

    const content = getDefaultContent();

    return (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-soft p-12 text-center animate-fade-in">
            {/* Illustration */}
            <div className="mb-6 animate-float">
                {getIllustration()}
            </div>

            {/* Content */}
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                {content.title}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-6">
                {content.description}
            </p>

            {/* Example Queries for Search State */}
            {type === 'search' && (
                <div className="mt-8 text-left max-w-md mx-auto">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center">
                        <svg className="h-4 w-4 mr-2 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Example queries:
                    </p>
                    <div className="space-y-2">
                        {[
                            'What is the punishment for murder?',
                            'How do I file an FIR?',
                            'What is anticipatory bail?',
                            'Difference between murder and culpable homicide?',
                        ].map((query, index) => (
                            <button
                                key={index}
                                onClick={() => {
                                    const searchInput = document.getElementById('search') as HTMLInputElement;
                                    if (searchInput) {
                                        searchInput.value = query;
                                        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                                        searchInput.focus();
                                    }
                                }}
                                className="block w-full text-left px-4 py-2 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-700 hover:bg-primary-50 dark:hover:bg-slate-600 hover:text-primary-600 dark:hover:text-primary-400 rounded-lg transition-all duration-300 group"
                            >
                                <span className="flex items-center">
                                    <svg className="h-4 w-4 mr-2 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                    {query}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Action Button */}
            {actionLabel && onAction && (
                <button
                    onClick={onAction}
                    className="mt-6 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-all duration-300 transform hover:-translate-y-0.5 hover:shadow-elevation-2"
                >
                    {actionLabel}
                </button>
            )}

            {/* Tips */}
            {type === 'search' && (
                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-slate-700">
                    <div className="flex items-start space-x-3 text-left max-w-md mx-auto">
                        <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg flex-shrink-0">
                            <svg className="h-5 w-5 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pro Tip</p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                                Use specific terms like section numbers or act names for better results. Press <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-slate-600 rounded text-xs">Ctrl+K</kbd> to quickly focus the search.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
