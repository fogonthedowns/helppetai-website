import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { History, Menu, X } from 'lucide-react';
import { SearchInterface } from '../components/search/SearchInterface';
import { AnswerDisplay } from '../components/search/AnswerDisplay';
import { SourcesPanel } from '../components/search/SourcesPanel';
import { LoadingState } from '../components/search/LoadingState';
import { SearchHistory } from '../components/search/SearchHistory';
import { useRAGSearch } from '../hooks/useRAGSearch';
import { useSearchHistory } from '../hooks/useSearchHistory';
import { combineSourceChunks, createCitationMapping, remapCitationsInAnswer } from '../utils/searchUtils';


export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const { 
    query, 
    isLoading, 
    result, 
    error, 
    searchId,
    search, 
    updateQuery,
    clearResults,
    clearError,
    cancelSearch 
  } = useRAGSearch();
  
  const { addSearch, hasSearches } = useSearchHistory();
  
  const [highlightedSourceIndex, setHighlightedSourceIndex] = useState<number | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Handle URL parameters (only search if explicitly navigated to with query)
  useEffect(() => {
    const urlQuery = searchParams.get('q');
    // Only auto-search on initial page load with a URL parameter
    // Don't auto-search when user manually clears the input
    if (urlQuery && !query && !result) {
      search(urlQuery);
    }
  }, [searchParams, search]);

  // Update URL when search completes successfully
  useEffect(() => {
    if (query && !isLoading && result) {
      const params = new URLSearchParams();
      params.set('q', query);
      if (searchId) {
        params.set('id', searchId);
      }
      setSearchParams(params, { replace: false });
    }
  }, [query, isLoading, result, searchId, setSearchParams]);

  // Add to history when search completes successfully
  useEffect(() => {
    if (result && !isLoading && query) {
      addSearch(query, result.answer);
    }
  }, [result, isLoading, query, addSearch]);

  const handleSearchStart = () => {
    clearError();
    setHighlightedSourceIndex(null);
  };

  const handleSearchComplete = () => {
    // Scroll to results on mobile
    if (isMobile && result) {
      setTimeout(() => {
        const resultsElement = document.getElementById('search-results');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    }
  };

  const handleCitationClick = (sourceIndex: number) => {
    if (result?.sources) {
      const combinedSources = combineSourceChunks(result.sources);
      const combinedSource = combinedSources[sourceIndex];
      if (combinedSource && combinedSource.chunks.length > 0) {
        setHighlightedSourceIndex(combinedSource.chunks[0].originalIndex);
      }
    }
    
    // Scroll to source on mobile
    if (isMobile) {
      setTimeout(() => {
        const sourcesElement = document.getElementById('sources-panel');
        if (sourcesElement) {
          sourcesElement.scrollIntoView({ behavior: 'smooth' });
        }
      }, 100);
    }
  };

  const handleCitationHover = (sourceIndex: number | null) => {
    if (!isMobile && sourceIndex !== null && result?.sources) {
      const combinedSources = combineSourceChunks(result.sources);
      const combinedSource = combinedSources[sourceIndex];
      if (combinedSource && combinedSource.chunks.length > 0) {
        setHighlightedSourceIndex(combinedSource.chunks[0].originalIndex);
      }
    } else if (sourceIndex === null) {
      setHighlightedSourceIndex(null);
    }
  };

  const handleHistorySearch = (selectedQuery: string, filters?: any) => {
    search(selectedQuery, filters);
    setShowHistory(false);
  };

  const hasResults = result && result.sources.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* RAG Search Header */}
      <div className="bg-white border-b border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Search</h1>
            
            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* History Button */}
              {hasSearches && (
                <button
                  onClick={() => setShowHistory(true)}
                  className="
                    flex items-center gap-2 px-3 py-2 text-sm font-medium
                    text-gray-600 hover:text-gray-900 hover:bg-gray-100
                    rounded-lg transition-colors
                  "
                >
                  <History className="w-4 h-4" />
                  {!isMobile && <span>History</span>}
                </button>
              )}

              {/* Mobile Menu Button */}
              {isMobile && hasResults && (
                <button
                  onClick={() => setShowHistory(true)}
                  className="
                    p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100
                    rounded-lg transition-colors
                  "
                >
                  <Menu className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Search Interface - Fixed at top */}
        <div className="pt-8 pb-6">
          <SearchInterface
            query={query}
            isLoading={isLoading}
            search={search}
            updateQuery={updateQuery}
            clearResults={clearResults}
            onSearchStart={handleSearchStart}
            onSearchComplete={handleSearchComplete}
            className="max-w-4xl"
          />
        </div>


        {/* Error Message */}
        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="text-red-600 mt-0.5">
                  ❌
                </div>
                <div>
                  <h3 className="font-medium text-red-900 mb-1">
                    Search Error
                  </h3>
                  <p className="text-red-800 text-sm">
                    {error}
                  </p>
                  <button
                    onClick={clearError}
                    className="mt-2 text-sm text-red-600 hover:text-red-800 font-medium"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="max-w-4xl mx-auto mt-8">
            <LoadingState onCancel={cancelSearch} />
          </div>
        )}

        {/* Results */}
        {hasResults && !isLoading && (
          <div id="search-results" className="space-y-6 mt-8">
            {/* Sources - Top and Compact */}
            <div id="sources-panel" className="max-w-5xl mx-auto">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                {(() => {
                  const combinedSources = combineSourceChunks(result.sources);
                  
                  return (
                    <>
                      <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                        Sources ({combinedSources.length})
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {combinedSources.slice(0, 6).map((combinedSource, index) => {
                          const handleSourceClick = () => {
                            if (combinedSource.url) {
                              window.open(combinedSource.url, '_blank', 'noopener,noreferrer');
                            } else {
                              // Highlight the first chunk of this source
                              setHighlightedSourceIndex(combinedSource.chunks[0].originalIndex);
                            }
                          };

                          // Extract domain from URL for display
                          const getUrlDomain = (url: string | null) => {
                            if (!url) return null;
                            try {
                              const domain = new URL(url).hostname;
                              return domain.replace('www.', '');
                            } catch {
                              return url;
                            }
                          };

                          return (
                            <div 
                              key={`combined-source-${combinedSource.id}-${index}`}
                              className={`
                                p-3 rounded-lg border cursor-pointer transition-all hover:shadow-sm
                                ${combinedSource.url ? 'hover:border-blue-400' : ''}
                                ${combinedSource.chunks.some(chunk => highlightedSourceIndex === chunk.originalIndex)
                                  ? 'border-blue-500 bg-blue-50' 
                                  : 'border-gray-200 bg-gray-50 hover:bg-gray-100'}
                              `}
                              onClick={handleSourceClick}
                              title={combinedSource.url ? `Click to open: ${combinedSource.url}` : 'Click to highlight in answer'}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                  {/* Source Number and Score */}
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white text-sm rounded-full flex items-center justify-center font-medium">
                                      {index + 1}
                                    </span>
                                    <span className="text-sm font-semibold text-green-700">
                                      {(combinedSource.maxRelevanceScore * 100).toFixed(0)}%
                                    </span>
                                    {combinedSource.url && (
                                      <span className="ml-auto text-blue-500"></span>
                                    )}
                                  </div>
                                  
                                  {/* Title */}
                                  <p className="text-sm font-medium text-gray-900 mb-2 line-clamp-2">
                                    {combinedSource.title || 'Veterinary Source'}
                                  </p>
                                  
                                  {/* URL Domain */}
                                  {combinedSource.url && (
                                    <p className="text-xs text-blue-600 truncate">
                                      {getUrlDomain(combinedSource.url)}
                                    </p>
                                  )}
                                  
                                  {/* Audience Badge */}
                                  {combinedSource.audience && (
                                    <div className="mt-2">
                                      <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                                        {combinedSource.audience}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>

            {/* Answer - Full Width */}
            <div className="max-w-5xl mx-auto">
              {(() => {
                const combinedSources = combineSourceChunks(result.sources);
                const citationMapping = createCitationMapping(result.sources, combinedSources);
                const remappedAnswer = remapCitationsInAnswer(result.answer, citationMapping);
                
                // Convert combined sources back to SourceReference format for AnswerDisplay
                const convertedSources = combinedSources.map(cs => ({
                  id: cs.id,
                  title: cs.title,
                  url: cs.url,
                  chunk_info: '', // Not needed for display
                  relevance_score: cs.maxRelevanceScore,
                  audience: cs.audience,
                  authority_level: cs.authority_level,
                  publisher: cs.publisher,
                  publication_year: cs.publication_year,
                  species: cs.species,
                  symptoms: cs.symptoms
                }));
                
                return (
                  <AnswerDisplay
                    result={{
                      ...result,
                      answer: remappedAnswer,
                      sources: convertedSources
                    }}
                    searchId={searchId || undefined}
                    onCitationClick={handleCitationClick}
                    onCitationHover={handleCitationHover}
                  />
                );
              })()}
            </div>
          </div>
        )}

        {/* No Results */}
        {result && result.sources.length === 0 && !isLoading && (
          <div className="max-w-4xl mx-auto text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-medium text-gray-900 mb-2">
              No sources found
            </h3>
            <p className="text-gray-600 mb-6">
              We couldn't find any relevant veterinary sources for your question.
              Try rephrasing your question or using different keywords.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="
                px-6 py-3 bg-blue-600 text-white font-medium rounded-lg
                hover:bg-blue-700 transition-colors
              "
            >
              Start New Search
            </button>
          </div>
        )}
      </main>

      {/* Search History Sidebar */}
      <SearchHistory
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onSearchSelect={handleHistorySearch}
      />

    </div>
  );
};
