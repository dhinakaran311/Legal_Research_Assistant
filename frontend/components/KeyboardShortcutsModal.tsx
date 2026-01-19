'use client';

import React, { useState } from 'react';

interface KeyboardShortcut {
    keys: string[];
    description: string;
    category: 'Navigation' | 'Search' | 'Actions';
}

const shortcuts: KeyboardShortcut[] = [
    { keys: ['Ctrl', 'K'], description: 'Focus search input', category: 'Search' },
    { keys: ['Esc'], description: 'Clear search / Close modals', category: 'Search' },
    { keys: ['Ctrl', 'Enter'], description: 'Submit search', category: 'Search' },
    { keys: ['Ctrl', '/'], description: 'Show keyboard shortcuts', category: 'Navigation' },
    { keys: ['↑', '↓'], description: 'Navigate search history', category: 'Navigation' },
    { keys: ['Ctrl', 'C'], description: 'Copy selected text', category: 'Actions' },
];

interface KeyboardShortcutsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
    if (!isOpen) return null;

    const categories = ['Search', 'Navigation', 'Actions'] as const;

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto animate-fade-in">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            ></div>

            {/* Modal */}
            <div className="flex min-h-full items-center justify-center p-4">
                <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-elevation-3 max-w-2xl w-full p-6 animate-slide-up border border-gray-200 dark:border-slate-700">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
                                <svg className="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                                Keyboard Shortcuts
                            </h2>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-all duration-300 transform hover:scale-110"
                        >
                            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Shortcuts by Category */}
                    <div className="space-y-6">
                        {categories.map((category) => {
                            const categoryShortcuts = shortcuts.filter(s => s.category === category);
                            if (categoryShortcuts.length === 0) return null;

                            return (
                                <div key={category}>
                                    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                                        {category}
                                    </h3>
                                    <div className="space-y-2">
                                        {categoryShortcuts.map((shortcut, index) => (
                                            <div
                                                key={index}
                                                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
                                            >
                                                <span className="text-sm text-gray-700 dark:text-gray-300">
                                                    {shortcut.description}
                                                </span>
                                                <div className="flex items-center space-x-1">
                                                    {shortcut.keys.map((key, i) => (
                                                        <React.Fragment key={i}>
                                                            <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-white dark:bg-slate-600 border border-gray-300 dark:border-slate-500 rounded shadow-sm">
                                                                {key}
                                                            </kbd>
                                                            {i < shortcut.keys.length - 1 && (
                                                                <span className="text-gray-400 dark:text-gray-500 text-xs">+</span>
                                                            )}
                                                        </React.Fragment>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Footer */}
                    <div className="mt-6 pt-4 border-t border-gray-200 dark:border-slate-700">
                        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                            Press <kbd className="px-1.5 py-0.5 text-xs bg-gray-200 dark:bg-slate-600 rounded">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 text-xs bg-gray-200 dark:bg-slate-600 rounded">/</kbd> anytime to view shortcuts
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
