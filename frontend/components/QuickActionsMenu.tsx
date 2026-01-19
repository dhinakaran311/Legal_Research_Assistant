'use client';

import React, { useState } from 'react';
import KeyboardShortcutsModal from './KeyboardShortcutsModal';

interface QuickAction {
    icon: React.ReactNode;
    label: string;
    onClick: () => void;
    color: string;
}

interface QuickActionsMenuProps {
    onShowShortcuts?: () => void;
}

export default function QuickActionsMenu({ onShowShortcuts }: QuickActionsMenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [showShortcuts, setShowShortcuts] = useState(false);

    const actions: QuickAction[] = [
        {
            icon: (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
            ),
            label: 'Keyboard Shortcuts',
            onClick: () => {
                setIsOpen(false);
                setShowShortcuts(true);
            },
            color: 'bg-blue-500 hover:bg-blue-600',
        },
        {
            icon: (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
            ),
            label: 'Quick Guide',
            onClick: () => {
                setIsOpen(false);
                // Could trigger a tutorial or guide
                alert('Quick Guide - Coming soon!');
            },
            color: 'bg-purple-500 hover:bg-purple-600',
        },
        {
            icon: (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            ),
            label: 'Help & Tips',
            onClick: () => {
                setIsOpen(false);
                // Could show tips carousel
                alert('Help & Tips - Coming soon!');
            },
            color: 'bg-green-500 hover:bg-green-600',
        },
        {
            icon: (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
            ),
            label: 'Scroll to Top',
            onClick: () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
                setIsOpen(false);
            },
            color: 'bg-indigo-500 hover:bg-indigo-600',
        },
    ];

    return (
        <>
            {/* FAB Menu */}
            <div className="fixed bottom-20 right-8 z-40">
                {/* Action Items */}
                <div className={`flex flex-col space-y-3 mb-3 transition-all duration-300 ${isOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}>
                    {actions.map((action, index) => (
                        <button
                            key={index}
                            onClick={action.onClick}
                            className={`${action.color} text-white p-3 rounded-full shadow-elevation-2 hover:shadow-elevation-3 transition-all duration-300 transform hover:scale-110 group relative`}
                            style={{ animationDelay: `${index * 50}ms` }}
                            title={action.label}
                        >
                            {action.icon}
                            {/* Tooltip */}
                            <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-gray-900 dark:bg-slate-700 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                                {action.label}
                            </span>
                        </button>
                    ))}
                </div>

                {/* Main FAB Button */}
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={`w-14 h-14 bg-gradient-primary text-white rounded-full shadow-elevation-3 hover:shadow-glass transition-all duration-300 transform hover:scale-110 ${isOpen ? 'rotate-45' : 'rotate-0'}`}
                    aria-label="Quick actions menu"
                >
                    <svg className="h-6 w-6 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                </button>
            </div>

            {/* Keyboard Shortcuts Modal */}
            <KeyboardShortcutsModal
                isOpen={showShortcuts}
                onClose={() => setShowShortcuts(false)}
            />
        </>
    );
}
