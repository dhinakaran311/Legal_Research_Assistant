'use client';

import React, { useState, useEffect } from 'react';

interface OnboardingStep {
    target: string;
    title: string;
    description: string;
    position: 'top' | 'bottom' | 'left' | 'right';
}

const onboardingSteps: OnboardingStep[] = [
    {
        target: '#search',
        title: 'Ask Your Legal Question',
        description: 'Type any legal question in plain English. Our AI will search through Indian legal acts and judgments.',
        position: 'bottom',
    },
    {
        target: '#use-llm',
        title: 'Enhanced AI Answers',
        description: 'Enable LLM for more conversational, synthesized answers. It\'s slower but provides better explanations.',
        position: 'top',
    },
    {
        target: '.theme-toggle',
        title: 'Dark Mode',
        description: 'Toggle between light and dark mode for comfortable reading at any time.',
        position: 'bottom',
    },
];

interface OnboardingTutorialProps {
    onComplete: () => void;
}

export default function OnboardingTutorial({ onComplete }: OnboardingTutorialProps) {
    const [currentStep, setCurrentStep] = useState(0);
    const [isVisible, setIsVisible] = useState(false);
    const [position, setPosition] = useState({ top: 0, left: 0 });

    useEffect(() => {
        // Check if user has seen tutorial
        const hasSeenTutorial = localStorage.getItem('hasSeenTutorial');
        if (!hasSeenTutorial) {
            setTimeout(() => setIsVisible(true), 1000);
        }
    }, []);

    useEffect(() => {
        if (isVisible && currentStep < onboardingSteps.length) {
            const step = onboardingSteps[currentStep];
            const element = document.querySelector(step.target);

            if (element) {
                const rect = element.getBoundingClientRect();
                const scrollY = window.scrollY;

                let top = 0;
                let left = 0;

                switch (step.position) {
                    case 'bottom':
                        top = rect.bottom + scrollY + 10;
                        left = rect.left + rect.width / 2;
                        break;
                    case 'top':
                        top = rect.top + scrollY - 10;
                        left = rect.left + rect.width / 2;
                        break;
                    case 'left':
                        top = rect.top + scrollY + rect.height / 2;
                        left = rect.left - 10;
                        break;
                    case 'right':
                        top = rect.top + scrollY + rect.height / 2;
                        left = rect.right + 10;
                        break;
                }

                setPosition({ top, left });

                // Highlight target element
                element.classList.add('onboarding-highlight');
                return () => element.classList.remove('onboarding-highlight');
            }
        }
    }, [currentStep, isVisible]);

    const handleNext = () => {
        if (currentStep < onboardingSteps.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            handleComplete();
        }
    };

    const handleSkip = () => {
        handleComplete();
    };

    const handleComplete = () => {
        setIsVisible(false);
        localStorage.setItem('hasSeenTutorial', 'true');
        onComplete();
    };

    if (!isVisible) return null;

    const step = onboardingSteps[currentStep];

    return (
        <>
            {/* Backdrop */}
            <div className="fixed inset-0 bg-black/60 z-[60] animate-fade-in backdrop-blur-sm"></div>

            {/* Tooltip */}
            <div
                className="fixed z-[70] animate-slide-up"
                style={{
                    top: `${position.top}px`,
                    left: `${position.left}px`,
                    transform: 'translateX(-50%)',
                }}
            >
                <div className="bg-white dark:bg-slate-800 rounded-xl shadow-elevation-3 p-5 max-w-sm border border-gray-200 dark:border-slate-700">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white pr-4">
                            {step.title}
                        </h3>
                        <button
                            onClick={handleSkip}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        >
                            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                        {step.description}
                    </p>

                    {/* Progress & Actions */}
                    <div className="flex items-center justify-between">
                        <div className="flex space-x-1">
                            {onboardingSteps.map((_, index) => (
                                <div
                                    key={index}
                                    className={`h-1.5 rounded-full transition-all duration-300 ${index === currentStep
                                            ? 'w-6 bg-primary-600'
                                            : index < currentStep
                                                ? 'w-1.5 bg-primary-400'
                                                : 'w-1.5 bg-gray-300 dark:bg-gray-600'
                                        }`}
                                ></div>
                            ))}
                        </div>

                        <div className="flex space-x-2">
                            <button
                                onClick={handleSkip}
                                className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                            >
                                Skip
                            </button>
                            <button
                                onClick={handleNext}
                                className="px-4 py-1.5 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                            >
                                {currentStep < onboardingSteps.length - 1 ? 'Next' : 'Got it!'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Arrow */}
                <div
                    className={`absolute bg-white dark:bg-slate-800 w-3 h-3 transform rotate-45 border-gray-200 dark:border-slate-700 ${step.position === 'bottom' ? '-top-1.5 left-1/2 -translate-x-1/2 border-t border-l' :
                            step.position === 'top' ? '-bottom-1.5 left-1/2 -translate-x-1/2 border-b border-r' :
                                ''
                        }`}
                ></div>
            </div>

            {/* Add highlight styles */}
            <style jsx global>{`
        .onboarding-highlight {
          position: relative;
          z-index: 65;
          box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.3), 0 0 0 9999px rgba(0, 0, 0, 0.6);
          border-radius: 8px;
        }
      `}</style>
        </>
    );
}
