import React, { useState, useEffect } from 'react';
import { BookOpen, Filter, SortAsc, SortDesc } from 'lucide-react';
import { SourceReference } from '../../types/rag';
import { SourceCard } from '../shared/SourceCard';

interface SourcesPanelProps {
  sources: SourceReference[];
  highlightedSourceIndex?: number | null;
  onSourceClick?: (index: number) => void;
  className?: string;
}

type SortOption = 'relevance' | 'title' | 'year' | 'authority';
type SortDirection = 'asc' | 'desc';

interface FilterOptions {
  audience?: string;
  species?: string[];
  authorityLevel?: string;
  minRelevance?: number;
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({
  sources,
  highlightedSourceIndex,
  onSourceClick,
  className = "",
}) => {
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [sortBy, setSortBy] = useState<SortOption>('relevance');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({});

  // Auto-expand highlighted source
  useEffect(() => {
    if (highlightedSourceIndex !== null && highlightedSourceIndex !== undefined) {
      setExpandedCards(prev => new Set(prev).add(highlightedSourceIndex));
    }
  }, [highlightedSourceIndex]);

  const toggleCardExpansion = (index: number) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const handleSort = (option: SortOption) => {
    if (sortBy === option) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(option);
      setSortDirection('desc');
    }
  };

  // Filter sources
  const filteredSources = sources.filter(source => {
    if (filters.audience && source.audience !== filters.audience) {
      return false;
    }
    
    if (filters.authorityLevel && source.authority_level !== filters.authorityLevel) {
      return false;
    }
    
    if (filters.minRelevance && source.relevance_score < filters.minRelevance) {
      return false;
    }
    
    if (filters.species && filters.species.length > 0) {
      const sourceSpecies = source.species || [];
      const hasMatchingSpecies = filters.species.some(species => 
        sourceSpecies.some(sourceSpecies => 
          sourceSpecies.toLowerCase().includes(species.toLowerCase())
        )
      );
      if (!hasMatchingSpecies) {
        return false;
      }
    }
    
    return true;
  });

  // Sort sources
  const sortedSources = [...filteredSources].sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'relevance':
        comparison = a.relevance_score - b.relevance_score;
        break;
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
      case 'year':
        comparison = (a.publication_year || 0) - (b.publication_year || 0);
        break;
      case 'authority':
        const authorityOrder = { 'expert': 3, 'academic': 2, 'clinical': 1 };
        const aAuth = authorityOrder[a.authority_level as keyof typeof authorityOrder] || 0;
        const bAuth = authorityOrder[b.authority_level as keyof typeof authorityOrder] || 0;
        comparison = aAuth - bAuth;
        break;
    }
    
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  // Get unique values for filters
  const uniqueAudiences = Array.from(new Set(sources.map(s => s.audience).filter((a): a is string => Boolean(a))));
  const uniqueAuthorities = Array.from(new Set(sources.map(s => s.authority_level).filter((a): a is string => Boolean(a))));
  const uniqueSpecies = Array.from(new Set(sources.flatMap(s => s.species || [])));

  const hasActiveFilters = Object.values(filters).some(value => 
    value && (Array.isArray(value) ? value.length > 0 : true)
  );

  if (sources.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-8 text-center ${className}`}>
        <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No sources found</h3>
        <p className="text-gray-600">Try adjusting your search query or filters.</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Sources ({filteredSources.length}{sources.length !== filteredSources.length && ` of ${sources.length}`})
            </h2>
          </div>

          <div className="flex items-center gap-2">
            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`
                flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors
                ${showFilters || hasActiveFilters
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              <Filter className="w-4 h-4" />
              <span>Filter</span>
              {hasActiveFilters && (
                <span className="bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {Object.values(filters).filter(v => v && (Array.isArray(v) ? v.length > 0 : true)).length}
                </span>
              )}
            </button>

            {/* Sort Options */}
            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              {[
                { key: 'relevance', label: 'Relevance' },
                { key: 'title', label: 'Title' },
                { key: 'year', label: 'Year' },
                { key: 'authority', label: 'Authority' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => handleSort(key as SortOption)}
                  className={`
                    flex items-center gap-1 px-2 py-1 text-xs font-medium rounded transition-colors
                    ${sortBy === key
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                    }
                  `}
                >
                  <span>{label}</span>
                  {sortBy === key && (
                    sortDirection === 'asc' ? 
                      <SortAsc className="w-3 h-3" /> : 
                      <SortDesc className="w-3 h-3" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="space-y-4 pt-4 border-t border-gray-100">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Audience Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Audience
                </label>
                <select
                  value={filters.audience || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, audience: e.target.value || undefined }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {uniqueAudiences.map(audience => (
                    <option key={audience} value={audience}>
                      {audience === 'pet-owner' ? 'Pet Owner' : 'Expert'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Authority Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Authority Level
                </label>
                <select
                  value={filters.authorityLevel || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, authorityLevel: e.target.value || undefined }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All</option>
                  {uniqueAuthorities.map(authority => (
                    <option key={authority} value={authority}>
                      {authority}
                    </option>
                  ))}
                </select>
              </div>

              {/* Relevance Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Min Relevance
                </label>
                <select
                  value={filters.minRelevance || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, minRelevance: e.target.value ? parseFloat(e.target.value) : undefined }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Any</option>
                  <option value="0.8">80%+</option>
                  <option value="0.6">60%+</option>
                  <option value="0.4">40%+</option>
                  <option value="0.2">20%+</option>
                </select>
              </div>

              {/* Species Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Species
                </label>
                <select
                  multiple
                  value={filters.species || []}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, option => option.value);
                    setFilters(prev => ({ ...prev, species: selected.length > 0 ? selected : undefined }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  size={3}
                >
                  {uniqueSpecies.map(species => (
                    <option key={species} value={species}>
                      {species}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <button
                onClick={() => setFilters({})}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Sources List */}
      <div className="p-6 space-y-4">
        {sortedSources.map((source, index) => {
          const originalIndex = sources.indexOf(source);
          return (
            <SourceCard
              key={`${source.id}-${source.chunk_info}-${originalIndex}`}
              source={source}
              index={originalIndex}
              isHighlighted={highlightedSourceIndex === originalIndex}
              isExpanded={expandedCards.has(originalIndex)}
              onToggleExpand={() => {
                toggleCardExpansion(originalIndex);
                onSourceClick?.(originalIndex);
              }}
            />
          );
        })}
      </div>
    </div>
  );
};
