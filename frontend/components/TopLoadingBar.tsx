'use client';

import { useEffect, useState } from 'react';

export default function TopLoadingBar() {
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        // Listen for navigation start/end
        const handleStart = () => {
            setIsLoading(true);
            setProgress(0);
        };

        const handleComplete = () => {
            setProgress(100);
            setTimeout(() => {
                setIsLoading(false);
                setProgress(0);
            }, 300);
        };

        // Simulate progress
        let interval: NodeJS.Timeout;
        if (isLoading && progress < 90) {
            interval = setInterval(() => {
                setProgress((prev) => {
                    const increment = Math.random() * 10;
                    return Math.min(prev + increment, 90);
                });
            }, 200);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isLoading, progress]);

    // Expose global functions for triggering
    useEffect(() => {
        (window as any).startLoading = () => {
            setIsLoading(true);
            setProgress(0);
        };
        (window as any).stopLoading = () => {
            setProgress(100);
            setTimeout(() => {
                setIsLoading(false);
                setProgress(0);
            }, 300);
        };
    }, []);

    if (!isLoading && progress === 0) return null;

    return (
        <div className="fixed top-0 left-0 right-0 z-[100] h-1 bg-transparent">
            <div
                className="h-full bg-gradient-to-r from-primary-500 via-primary-600 to-primary-500 transition-all duration-200 ease-out shadow-lg"
                style={{
                    width: `${progress}%`,
                    boxShadow: '0 0 10px rgba(14, 165, 233, 0.5)',
                }}
            >
                {/* Shimmer effect */}
                <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
            </div>
        </div>
    );
}
