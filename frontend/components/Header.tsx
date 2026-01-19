'use client';

import React from 'react';
import Link from 'next/link';
import { useTheme } from '@/contexts/ThemeContext';

interface HeaderProps {
    user?: {
        name: string;
        email: string;
    } | null;
    onLogout?: () => void;
    showAuth?: boolean;
}

export default function Header({ user, onLogout, showAuth = true }: HeaderProps) {
    const { theme, toggleTheme } = useTheme();

    return (
        <header className="bg-white dark:bg-slate-800 shadow-sm sticky top-0 z-50 transition-colors duration-300 backdrop-blur-sm bg-opacity-90 dark:bg-opacity-90">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex justify-between items-center">
                    <Link href={user ? '/search' : '/'} className="flex items-center space-x-3 group">
                        <div className="relative">
                            <div className="absolute inset-0 bg-primary-600 rounded-lg blur opacity-25 group-hover:opacity-50 transition-opacity"></div>
                            <div className="relative bg-gradient-primary p-2 rounded-lg transform group-hover:scale-110 transition-transform duration-300">
                                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                                </svg>
                            </div>
                        </div>
                        <div>
                            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white transition-colors">
                                Legal Research Assistant
                            </h1>
                            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 transition-colors">
                                AI-powered legal research
                            </p>
                        </div>
                    </Link>

                    <div className="flex items-center space-x-3">
                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 transition-all duration-300 transform hover:scale-110"
                            aria-label="Toggle theme"
                        >
                            {theme === 'light' ? (
                                <svg className="h-5 w-5 text-gray-700 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                                </svg>
                            ) : (
                                <svg className="h-5 w-5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                                </svg>
                            )}
                        </button>

                        {/* User Menu */}
                        {showAuth && user && (
                            <>
                                <div className="hidden sm:block text-right">
                                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        {user.name}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {user.email}
                                    </p>
                                </div>
                                <button
                                    onClick={onLogout}
                                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-700 border border-gray-300 dark:border-slate-600 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-600 transition-all duration-300 hover:shadow-md transform hover:-translate-y-0.5"
                                >
                                    Logout
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
