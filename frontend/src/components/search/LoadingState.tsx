import React, { useState, useEffect } from 'react';
import { Search, Database, Brain, X } from 'lucide-react';
import { LoadingPhase } from '../../types/rag';

interface LoadingStateProps {
  onCancel?: () => void;
  className?: string;
}

const LOADING_PHASES: LoadingPhase[] = [
  {
    id: 'search',
    message: 'Searching knowledge base...',
    duration: 3,
    icon: 'search',
  },
  {
    id: 'analyze',
    message: 'Analyzing veterinary sources...',
    duration: 5,
    icon: 'database',
  },
  {
    id: 'generate',
    message: 'Generating expert response...',
    duration: 8,
    icon: 'brain',
  },
];

const getIcon = (iconName: string) => {
  switch (iconName) {
    case 'search':
      return Search;
    case 'database':
      return Database;
    case 'brain':
      return Brain;
    default:
      return Search;
  }
};

export const LoadingState: React.FC<LoadingStateProps> = ({
  onCancel,
  className = "",
}) => {
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [dots, setDots] = useState('');

  const currentPhase = LOADING_PHASES[currentPhaseIndex];
  const IconComponent = getIcon(currentPhase.icon);

  // Update elapsed time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Progress to next phase based on elapsed time
  useEffect(() => {
    const totalDuration = LOADING_PHASES.slice(0, currentPhaseIndex + 1)
      .reduce((sum, phase) => sum + phase.duration, 0);

    if (elapsedTime >= totalDuration && currentPhaseIndex < LOADING_PHASES.length - 1) {
      setCurrentPhaseIndex(prev => prev + 1);
    }
  }, [elapsedTime, currentPhaseIndex]);

  // Animated dots effect
  useEffect(() => {
    const dotsTimer = setInterval(() => {
      setDots(prev => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(dotsTimer);
  }, []);

  const progressPercentage = Math.min(
    (elapsedTime / LOADING_PHASES.reduce((sum, phase) => sum + phase.duration, 0)) * 100,
    100
  );

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Processing your question
          </h2>
          
          {onCancel && (
            <button
              onClick={onCancel}
              className="
                p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100
                rounded-lg transition-colors
              "
              title="Cancel search"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Loading Content */}
      <div className="p-8">
        {/* Current Phase */}
        <div className="text-center mb-8">
          {/* Animated Icon */}
          <div className="relative mx-auto w-16 h-16 mb-4">
            <div className="
              absolute inset-0 bg-blue-100 rounded-full animate-ping
            " style={{ animationDuration: '2s' }} />
            <div className="
              relative bg-blue-600 text-white rounded-full w-16 h-16
              flex items-center justify-center
            ">
              <IconComponent className="w-8 h-8" />
            </div>
          </div>

          {/* Current Message */}
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            {currentPhase.message}{dots}
          </h3>
          
          {/* Elapsed Time */}
          <p className="text-sm text-gray-600">
            {elapsedTime}s elapsed
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Phase Indicators */}
        <div className="space-y-3">
          {LOADING_PHASES.map((phase, index) => {
            const PhaseIcon = getIcon(phase.icon);
            const isActive = index === currentPhaseIndex;
            const isCompleted = index < currentPhaseIndex;
            const isPending = index > currentPhaseIndex;

            return (
              <div
                key={phase.id}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-all duration-500
                  ${isActive 
                    ? 'bg-blue-50 border border-blue-200' 
                    : isCompleted
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-gray-50 border border-gray-200'
                  }
                `}
              >
                {/* Phase Icon */}
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center transition-colors
                  ${isActive
                    ? 'bg-blue-600 text-white'
                    : isCompleted
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-400 text-white'
                  }
                `}>
                  {isCompleted ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <PhaseIcon className="w-4 h-4" />
                  )}
                </div>

                {/* Phase Text */}
                <div className="flex-1">
                  <span className={`
                    font-medium transition-colors
                    ${isActive
                      ? 'text-blue-900'
                      : isCompleted
                      ? 'text-green-900'
                      : 'text-gray-600'
                    }
                  `}>
                    {phase.message}
                  </span>
                  
                  {isActive && (
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" />
                      <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                      <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                    </div>
                  )}
                </div>

                {/* Duration Badge */}
                <span className={`
                  text-xs px-2 py-1 rounded-full
                  ${isActive
                    ? 'bg-blue-100 text-blue-700'
                    : isCompleted
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-600'
                  }
                `}>
                  ~{phase.duration}s
                </span>
              </div>
            );
          })}
        </div>

        {/* Long Running Warning */}
        {elapsedTime > 20 && (
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-5 h-5 text-yellow-600 mt-0.5">
                ⚠️
              </div>
              <div>
                <h4 className="font-medium text-yellow-900 mb-1">
                  Taking longer than expected
                </h4>
                <p className="text-sm text-yellow-800">
                  Your query is complex and requires more processing time. 
                  This is normal for detailed veterinary questions.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
