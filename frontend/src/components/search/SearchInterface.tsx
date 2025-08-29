import React, { useState, useRef, useEffect } from 'react';
import { Search, X, Filter } from 'lucide-react';
import { debounce } from '../../utils/searchUtils';
import { RAGRequest } from '../../types/rag';

interface SearchInterfaceProps {
  query: string;
  isLoading: boolean;
  search: (query: string, filters?: any) => Promise<void>;
  updateQuery: (query: string) => void;
  clearResults: () => void;
  onSearchStart?: () => void;
  onSearchComplete?: () => void;
  className?: string;
}



export const SearchInterface: React.FC<SearchInterfaceProps> = ({
  query,
  isLoading,
  search,
  updateQuery,
  clearResults,
  onSearchStart,
  onSearchComplete,
  className = "",
}) => {

  
  const [isFocused, setIsFocused] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  // Local filter state
  const [localFilters, setLocalFilters] = useState<Partial<RAGRequest>>({
    audience: undefined,
    species: [],
    symptoms: [],
    doc_type: undefined,
  });

  // Applied filter state (filters that are currently active for searches)
  const [appliedFilters, setAppliedFilters] = useState<Partial<RAGRequest>>({});
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Helper function to check if any filters are active
  const hasActiveFilters = () => {
    return !!(
      appliedFilters.audience ||
      (appliedFilters.species && appliedFilters.species.length > 0) ||
      (appliedFilters.symptoms && appliedFilters.symptoms.length > 0) ||
      appliedFilters.doc_type
    );
  };

  // Auto-resize textarea
  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      // Reset height to auto to get the correct scrollHeight
      textareaRef.current.style.height = 'auto';
      
      // Calculate the new height (between 60px and 200px)
      const scrollHeight = textareaRef.current.scrollHeight;
      const newHeight = Math.max(60, Math.min(scrollHeight, 200));
      
      // Set the new height
      textareaRef.current.style.height = `${newHeight}px`;
    }
  };

  // Debounced search function
  const debouncedSearch = debounce((searchQuery: string) => {
    if (searchQuery.trim()) {
      onSearchStart?.();
      search(searchQuery).finally(() => {
        onSearchComplete?.();
      });
    }
  }, 300);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    updateQuery(value);
    adjustTextareaHeight();
    

  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearchStart?.();
      search(query, appliedFilters).finally(() => {
        onSearchComplete?.();
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    } else if (e.key === 'Escape') {
      handleClear();
      textareaRef.current?.blur();
    }
  };

  const handleClear = () => {
    updateQuery('');
    clearResults();
    adjustTextareaHeight();
  };



  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    // Delay to allow recent search clicks
    setTimeout(() => {
      setIsFocused(false);
    }, 200);
  };



  // Auto-focus on mount and adjust height
  useEffect(() => {
    if (textareaRef.current) {
      if (!query) {
        textareaRef.current.focus();
      }
      // Always adjust height on mount in case there's pre-filled text
      // Use setTimeout to ensure DOM is fully rendered
      setTimeout(() => {
        adjustTextareaHeight();
      }, 0);
    }
  }, []);

  // Sync local filters with applied filters when filter panel opens
  useEffect(() => {
    if (showFilters) {
      setLocalFilters(appliedFilters);
    }
  }, [showFilters, appliedFilters]);

  // Adjust height when query changes
  useEffect(() => {
    adjustTextareaHeight();
  }, [query]);



  return (
    <div ref={containerRef} className={`relative w-full max-w-4xl mx-auto ${className}`}>
      {/* Main Search Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className={`
          relative border-2 rounded-2xl bg-white shadow-lg transition-all duration-200
          ${isFocused ? 'border-blue-500 shadow-xl' : 'border-gray-200'}
          ${isLoading ? 'pointer-events-none opacity-75' : ''}
        `}>
          {/* Search Icon */}
          <div className="absolute left-6 top-1/2 transform -translate-y-1/2 z-10">
            <Search className={`w-6 h-6 transition-colors ${isFocused ? 'text-blue-500' : 'text-gray-400'}`} />
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder="Ask a veterinary question..."
            className="
              w-full pl-16 pr-44 py-4 text-lg bg-transparent border-none outline-none resize-none
              placeholder-gray-400 text-gray-800 leading-relaxed overflow-hidden
            "
            rows={1}
            disabled={isLoading}
            style={{ minHeight: '60px', maxHeight: '200px', height: 'auto' }}
          />

          {/* Right Side Actions */}
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
            {/* Filter Button */}
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`
                relative p-2 rounded-lg transition-colors
                ${showFilters || hasActiveFilters() ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600'}
              `}
              title={hasActiveFilters() ? "Filters active - click to modify" : "Filter search"}
            >
              <Filter className="w-5 h-5" />
              {hasActiveFilters() && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">!</span>
                </span>
              )}
            </button>

            {/* Clear Button */}
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-lg"
                title="Clear search"
              >
                <X className="w-5 h-5" />
              </button>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className={`
                px-4 py-2 rounded-lg font-medium transition-all
                ${query.trim() && !isLoading
                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-gray-300 border-t-white rounded-full animate-spin" />
                  <span>Searching...</span>
                </div>
              ) : (
                'Search'
              )}
            </button>
          </div>
        </div>
      </form>



      {/* Filter Panel - Properly spaced below search */}
      {showFilters && (
        <div className="mt-4 bg-white border border-gray-200 rounded-xl shadow-lg p-4 max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900">Search Filters</h3>
            <button
              onClick={() => setShowFilters(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-4">
            {/* Audience Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Audience</label>
              <div className="flex gap-2">
                {['expert', 'pet-owner'].map((option) => (
                  <button
                    key={option}
                    onClick={() => {
                      setLocalFilters(prev => ({
                        ...prev, 
                        audience: prev.audience === option ? undefined : option as 'expert' | 'pet-owner'
                      }));
                    }}
                    className={`
                      px-3 py-1.5 text-sm rounded-full border transition-colors
                      ${localFilters.audience === option
                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    {option === 'expert' ? '👩‍⚕️ Expert' : '🐾 Pet Owner'}
                  </button>
                ))}
              </div>
            </div>

            {/* Species Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Species</label>
              <div className="flex flex-wrap gap-2">
                {[
                  { value: 'dog', label: '🐕 Dog' },
                  { value: 'cat', label: '🐱 Cat' },
                  { value: 'horse', label: '🐴 Horse' },
                  { value: 'bird', label: '🐦 Bird' },
                  { value: 'rabbit', label: '🐰 Rabbit' },
                  { value: 'reptile', label: '🦎 Reptile' }
                ].map((species) => (
                  <button
                    key={species.value}
                    onClick={() => {
                      const currentSpecies = localFilters.species || [];
                      const isSelected = currentSpecies.includes(species.value);
                      setLocalFilters(prev => ({
                        ...prev,
                        species: isSelected 
                          ? currentSpecies.filter(s => s !== species.value)
                          : [...currentSpecies, species.value]
                      }));
                    }}
                    className={`
                      px-3 py-1.5 text-sm rounded-full border transition-colors
                      ${(localFilters.species || []).includes(species.value)
                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    {species.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Symptoms Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Common Conditions</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  'Diarrhea', 'Vomiting', 'Fever', 'Bloat',
                  'Kidney Disease', 'Diabetes', 'Arthritis', 'Seizures',
                  'Respiratory', 'Skin Conditions', 'Parasites', 'Dental'
                ].map((symptom) => (
                  <button
                    key={symptom}
                    onClick={() => {
                      const currentSymptoms = localFilters.symptoms || [];
                      const isSelected = currentSymptoms.includes(symptom.toLowerCase());
                      setLocalFilters(prev => ({
                        ...prev,
                        symptoms: isSelected 
                          ? currentSymptoms.filter(s => s !== symptom.toLowerCase())
                          : [...currentSymptoms, symptom.toLowerCase()]
                      }));
                    }}
                    className={`
                      px-3 py-2 text-sm rounded-lg border transition-colors text-left
                      ${(localFilters.symptoms || []).includes(symptom.toLowerCase())
                        ? 'bg-green-100 border-green-300 text-green-800'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    {symptom}
                  </button>
                ))}
              </div>
            </div>

            {/* Document Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Document Type</label>
              <div className="flex gap-2">
                {['PDF', 'Article', 'Guideline', 'Textbook'].map((type) => (
                  <button
                    key={type}
                    onClick={() => {
                      setLocalFilters(prev => ({
                        ...prev, 
                        doc_type: prev.doc_type === type ? undefined : type
                      }));
                    }}
                    className={`
                      px-3 py-1.5 text-sm rounded-full border transition-colors
                      ${localFilters.doc_type === type
                        ? 'bg-purple-100 border-purple-300 text-purple-800'
                        : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    📄 {type}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
            <button 
              onClick={() => {
                // Clear both local and applied filters
                setLocalFilters({
                  audience: undefined,
                  species: [],
                  symptoms: [],
                  doc_type: undefined,
                });
                setAppliedFilters({});
              }}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear All
            </button>
            <button 
              onClick={() => {
                // Apply filters (store them as active filters)
                setAppliedFilters(localFilters);
                setShowFilters(false);
                // Note: User must manually trigger search by clicking search button or pressing Enter
              }}
              className="px-6 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}

      {/* Active Filters Display */}
      {hasActiveFilters() && !showFilters && (
        <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-blue-50 border border-blue-200 rounded-lg z-40">
          <div className="flex items-center justify-between">
            <div className="flex flex-wrap gap-1 text-xs">
              <span className="text-blue-700 font-medium">Active filters:</span>
              {appliedFilters.audience && (
                <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full">
                  {appliedFilters.audience}
                </span>
              )}
              {appliedFilters.species && appliedFilters.species.length > 0 && (
                <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded-full">
                  {appliedFilters.species.length} species
                </span>
              )}
              {appliedFilters.symptoms && appliedFilters.symptoms.length > 0 && (
                <span className="bg-green-200 text-green-800 px-2 py-1 rounded-full">
                  {appliedFilters.symptoms.length} symptoms
                </span>
              )}
              {appliedFilters.doc_type && (
                <span className="bg-purple-200 text-purple-800 px-2 py-1 rounded-full">
                  {appliedFilters.doc_type}
                </span>
              )}
            </div>
            <button
              onClick={() => {
                // Clear both local and applied filters
                setLocalFilters({
                  audience: undefined,
                  species: [],
                  symptoms: [],
                  doc_type: undefined,
                });
                setAppliedFilters({});
              }}
              className="text-blue-600 hover:text-blue-800 text-xs"
            >
              Clear all
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
