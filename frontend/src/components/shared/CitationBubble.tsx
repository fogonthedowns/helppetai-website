import React, { useState } from 'react';
import { SourceReference } from '../../types/rag';

interface CitationBubbleProps {
  number: number;
  source?: SourceReference;
  onClick?: () => void;
  onHover?: (isHovering: boolean) => void;
  className?: string;
}

export const CitationBubble: React.FC<CitationBubbleProps> = ({
  number,
  source,
  onClick,
  onHover,
  className = "",
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = () => {
    setIsHovered(true);
    onHover?.(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    onHover?.(false);
  };

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onClick?.();
  };

  return (
    <>
      <button
        onClick={handleClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className={`
          inline-flex items-center justify-center w-6 h-6 ml-1 text-xs font-bold 
          rounded-full transition-all duration-200 cursor-pointer
          ${isHovered 
            ? 'bg-blue-600 text-white scale-110 shadow-lg' 
            : 'bg-blue-500 text-white hover:bg-blue-600'
          }
          ${className}
        `}
        title={source ? `Source: ${source.title}` : `Citation ${number}`}
        aria-label={`Citation ${number}${source ? `: ${source.title}` : ''}`}
      >
        {number}
      </button>

      {/* Tooltip */}
      {isHovered && source && (
        <div className="
          fixed z-50 px-3 py-2 text-sm bg-gray-900 text-white rounded-lg shadow-lg
          pointer-events-none transform -translate-x-1/2 -translate-y-full
          max-w-xs whitespace-normal
        "
        style={{
          left: '50%',
          top: '-8px',
        }}>
          <div className="font-medium">{source.title}</div>
          {source.publisher && (
            <div className="text-gray-300 text-xs mt-1">{source.publisher}</div>
          )}
          {source.relevance_score && (
            <div className="text-gray-300 text-xs">
              Relevance: {(source.relevance_score * 100).toFixed(0)}%
            </div>
          )}
          
          {/* Arrow */}
          <div className="
            absolute top-full left-1/2 transform -translate-x-1/2
            w-0 h-0 border-l-4 border-r-4 border-t-4
            border-l-transparent border-r-transparent border-t-gray-900
          " />
        </div>
      )}
    </>
  );
};
