import React, { useState } from 'react';
import { ExternalLink, Calendar, Users, Star, ChevronDown, ChevronRight } from 'lucide-react';
import { SourceReference } from '../../types/rag';
import { getSpeciesEmoji, getAuthorityBadge, getRelevanceStars, formatTimestamp } from '../../utils/searchUtils';

interface SourceCardProps {
  source: SourceReference;
  index: number;
  isHighlighted?: boolean;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  className?: string;
}

export const SourceCard: React.FC<SourceCardProps> = ({
  source,
  index,
  isHighlighted = false,
  isExpanded = false,
  onToggleExpand,
  className = "",
}) => {
  const [imageError, setImageError] = useState(false);

  const citationNumber = index + 1;
  const authorityBadge = getAuthorityBadge(source.authority_level);
  const relevanceStars = getRelevanceStars(source.relevance_score);

  const handleExternalLinkClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (source.url) {
      window.open(source.url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div
      className={`
        bg-white border rounded-lg transition-all duration-200 cursor-pointer
        ${isHighlighted 
          ? 'border-blue-500 shadow-lg ring-2 ring-blue-200' 
          : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
        }
        ${className}
      `}
      onClick={onToggleExpand}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          {/* Citation Number & Title */}
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {/* Citation Bubble */}
            <div className={`
              flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
              text-sm font-bold text-white
              ${isHighlighted ? 'bg-blue-600' : 'bg-blue-500'}
            `}>
              {citationNumber}
            </div>

            {/* Title & Publisher */}
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {source.title}
              </h3>
              
              {source.publisher && (
                <p className="text-sm text-gray-600 mt-1">
                  {source.publisher}
                </p>
              )}
            </div>

            {/* Authority Badge */}
            <div className={`
              flex-shrink-0 px-2 py-1 rounded-full text-xs font-medium
              ${authorityBadge.color}
            `}>
              <span className="mr-1">{authorityBadge.emoji}</span>
              {authorityBadge.label}
            </div>
          </div>

          {/* Expand/Collapse Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand?.();
            }}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors ml-2"
          >
            {isExpanded ? (
              <ChevronDown className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Metadata Row */}
        <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
          {/* Publication Year */}
          {source.publication_year && (
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>{source.publication_year}</span>
            </div>
          )}

          {/* Audience */}
          {source.audience && (
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              <span className="capitalize">
                {source.audience === 'pet-owner' ? '🐾 Pet Owner' : '🩺 Expert'}
              </span>
            </div>
          )}

          {/* Relevance Score */}
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4" />
            <div className="flex items-center gap-1">
              {Array.from({ length: 5 }, (_, i) => (
                <Star
                  key={i}
                  className={`w-3 h-3 ${
                    i < relevanceStars ? 'text-yellow-400 fill-current' : 'text-gray-300'
                  }`}
                />
              ))}
              <span className="ml-1 text-xs">
                {(source.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Species Tags */}
        {source.species && source.species.length > 0 && (
          <div className="flex items-center gap-2 mt-3">
            <span className="text-sm text-gray-600">Species:</span>
            <div className="flex flex-wrap gap-1">
              {source.species.map((species, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                >
                  <span>{getSpeciesEmoji(species)}</span>
                  <span className="capitalize">{species}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Symptoms Tags */}
        {source.symptoms && source.symptoms.length > 0 && (
          <div className="flex items-center gap-2 mt-2">
            <span className="text-sm text-gray-600">Symptoms:</span>
            <div className="flex flex-wrap gap-1">
              {source.symptoms.slice(0, 3).map((symptom, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full capitalize"
                >
                  {symptom.replace(/-/g, ' ')}
                </span>
              ))}
              {source.symptoms.length > 3 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                  +{source.symptoms.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-100 p-4 bg-gray-50">
          {/* Chunk Info */}
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-600">
              {source.chunk_info}
            </span>
            
            {/* External Link */}
            {source.url && (
              <button
                onClick={handleExternalLinkClick}
                className="
                  flex items-center gap-1 px-3 py-1.5 text-sm font-medium
                  text-blue-600 hover:text-blue-800 hover:bg-blue-50
                  rounded-lg transition-colors
                "
              >
                <span>View Source</span>
                <ExternalLink className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Additional Metadata */}
          <div className="text-xs text-gray-500 space-y-1">
            <div>Source ID: {source.id}</div>
            <div>Relevance Score: {source.relevance_score.toFixed(4)}</div>
          </div>
        </div>
      )}
    </div>
  );
};
