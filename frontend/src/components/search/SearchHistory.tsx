import React, { useState } from 'react';
import { History, Search, Trash2, X, Clock, Filter } from 'lucide-react';
import { useSearchHistory } from '../../hooks/useSearchHistory';
import { formatTimestamp, getSpeciesEmoji } from '../../utils/searchUtils';

interface SearchHistoryProps {
  isOpen: boolean;
  onClose: () => void;
  onSearchSelect: (query: string, filters?: any) => void;
  className?: string;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({
  isOpen,
  onClose,
  onSearchSelect,
  className = "",
}) => {
  const { 
    history, 
    hasSearches, 
    removeSearch, 
    clearHistory, 
    searchHistory 
  } = useSearchHistory();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [showConfirmClear, setShowConfirmClear] = useState(false);

  const filteredHistory = searchTerm ? searchHistory(searchTerm) : history;

  const handleSearchSelect = (item: any) => {
    onSearchSelect(item.query, item.filters);
    onClose();
  };

  const handleRemoveSearch = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    removeSearch(id);
  };

  const handleClearHistory = () => {
    clearHistory();
    setShowConfirmClear(false);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className={`
        fixed top-0 right-0 h-full w-96 bg-white shadow-xl z-50
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        ${className}
      `}>
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <History className="w-6 h-6 text-gray-700" />
              <h2 className="text-xl font-semibold text-gray-900">
                Search History
              </h2>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Search Input */}
          {hasSearches && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search history..."
                className="
                  w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  text-sm
                "
              />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {!hasSearches ? (
            /* Empty State */
            <div className="p-8 text-center">
              <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No search history
              </h3>
              <p className="text-gray-600">
                Your recent searches will appear here for easy access.
              </p>
            </div>
          ) : filteredHistory.length === 0 ? (
            /* No Results */
            <div className="p-8 text-center">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No matching searches
              </h3>
              <p className="text-gray-600">
                Try a different search term.
              </p>
            </div>
          ) : (
            /* History List */
            <div className="p-4 space-y-3">
              {filteredHistory.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSearchSelect(item)}
                  className="
                    group p-4 border border-gray-200 rounded-lg cursor-pointer
                    hover:border-gray-300 hover:shadow-sm transition-all
                    bg-white hover:bg-gray-50
                  "
                >
                  {/* Main Content */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      {/* Query */}
                      <h4 className="font-medium text-gray-900 mb-1 line-clamp-2">
                        {item.query}
                      </h4>
                      
                      {/* Preview */}
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {item.preview}
                      </p>

                      {/* Filters */}
                      {item.filters && Object.keys(item.filters).length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {item.filters.species && item.filters.species.length > 0 && (
                            <div className="flex items-center gap-1">
                              {item.filters.species.slice(0, 2).map((species: string, idx: number) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                                >
                                  <span>{getSpeciesEmoji(species)}</span>
                                  <span>{species}</span>
                                </span>
                              ))}
                              {item.filters.species.length > 2 && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                  +{item.filters.species.length - 2}
                                </span>
                              )}
                            </div>
                          )}
                          
                          {item.filters.audience && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              <Filter className="w-3 h-3" />
                              <span>{item.filters.audience}</span>
                            </span>
                          )}
                        </div>
                      )}

                      {/* Timestamp */}
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        <span>{formatTimestamp(item.timestamp)}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => handleRemoveSearch(e, item.id)}
                        className="
                          p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50
                          rounded transition-colors
                        "
                        title="Remove from history"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {hasSearches && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            {!showConfirmClear ? (
              <button
                onClick={() => setShowConfirmClear(true)}
                className="
                  w-full px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700
                  hover:bg-red-50 border border-red-200 hover:border-red-300
                  rounded-lg transition-colors
                "
              >
                Clear All History
              </button>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-gray-700 text-center">
                  Are you sure you want to clear all search history?
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleClearHistory}
                    className="
                      flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600
                      hover:bg-red-700 rounded-lg transition-colors
                    "
                  >
                    Clear All
                  </button>
                  <button
                    onClick={() => setShowConfirmClear(false)}
                    className="
                      flex-1 px-4 py-2 text-sm font-medium text-gray-700
                      hover:bg-gray-100 border border-gray-300 rounded-lg transition-colors
                    "
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};
