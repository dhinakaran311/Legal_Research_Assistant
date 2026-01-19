'use client';

import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    text?: string;
}

export function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'h-8 w-8',
        md: 'h-12 w-12',
        lg: 'h-16 w-16',
    };

    return (
        <div className="flex flex-col items-center justify-center">
            <div className="relative">
                <div className={`${sizeClasses[size]} rounded-full border-4 border-gray-200 dark:border-gray-700`}></div>
                <div className={`${sizeClasses[size]} absolute top-0 rounded-full border-4 border-primary-600 border-t-transparent animate-spin`}></div>
            </div>
            {text && (
                <p className="mt-4 text-gray-600 dark:text-gray-400 animate-pulse">{text}</p>
            )}
        </div>
    );
}

export function SkeletonLoader({ type = 'card' }: { type?: 'card' | 'text' | 'header' }) {
    if (type === 'header') {
        return (
            <div className="animate-pulse space-y-4">
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
        );
    }

    if (type === 'text') {
        return (
            <div className="animate-pulse space-y-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-6 space-y-4 animate-pulse">
            <div className="flex items-center space-x-4">
                <div className="h-12 w-12 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                </div>
            </div>
            <div className="space-y-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
            </div>
        </div>
    );
}

export function SearchResultsSkeleton() {
    return (
        <div className="space-y-6 animate-fade-in">
            {/* Answer Section Skeleton */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-6 border-l-4 border-primary-600">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
                    <div className="space-y-2">
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                    </div>
                </div>
            </div>

            {/* Sources Section Skeleton */}
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-6">
                <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/6 mb-4"></div>
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 animate-pulse">
                            <div className="flex items-center space-x-2 mb-2">
                                <div className="h-6 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                                <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                            </div>
                            <div className="space-y-2">
                                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
                                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
