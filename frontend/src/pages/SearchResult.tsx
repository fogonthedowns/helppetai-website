import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { Share2, ArrowLeft, ExternalLink } from 'lucide-react';
import { SearchPage } from './SearchPage';
import { copyToClipboard } from '../utils/searchUtils';

export const SearchResult: React.FC = () => {
  const { searchId } = useParams<{ searchId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [shareSuccess, setShareSuccess] = useState(false);

  const query = searchParams.get('q');

  useEffect(() => {
    // If no search ID or query, redirect to home
    if (!searchId && !query) {
      navigate('/', { replace: true });
    }
  }, [searchId, query, navigate]);

  const handleShare = async () => {
    const currentUrl = window.location.href;
    const success = await copyToClipboard(currentUrl);
    
    if (success) {
      setShareSuccess(true);
      setTimeout(() => setShareSuccess(false), 2000);
    }
  };

  const handleBackToSearch = () => {
    navigate('/rag');
  };

  // Use the same SearchPage component but with additional header for shared results
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Shared Result Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Back Button */}
            <button
              onClick={handleBackToSearch}
              className="
                flex items-center gap-2 px-3 py-2 text-sm font-medium
                text-gray-600 hover:text-gray-900 hover:bg-gray-100
                rounded-lg transition-colors
              "
            >
              <ArrowLeft className="w-4 h-4" />
              <span>New Search</span>
            </button>

            {/* Share Actions */}
            <div className="flex items-center gap-2">
              {/* Share Button */}
              <button
                onClick={handleShare}
                className="
                  flex items-center gap-2 px-3 py-2 text-sm font-medium
                  text-gray-600 hover:text-gray-900 hover:bg-gray-100
                  rounded-lg transition-colors
                "
              >
                <Share2 className="w-4 h-4" />
                <span>{shareSuccess ? 'Copied!' : 'Share'}</span>
              </button>

              {/* Open in New Tab */}
              <button
                onClick={() => window.open(window.location.href, '_blank')}
                className="
                  flex items-center gap-2 px-3 py-2 text-sm font-medium
                  text-gray-600 hover:text-gray-900 hover:bg-gray-100
                  rounded-lg transition-colors
                "
              >
                <ExternalLink className="w-4 h-4" />
                <span>Open in New Tab</span>
              </button>
            </div>
          </div>

          {/* Shared Result Info */}
          {query && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="text-blue-600 text-xl">🔗</div>
                <div>
                  <h3 className="font-medium text-blue-900 mb-1">
                    Shared Search Result
                  </h3>
                  <p className="text-blue-800 text-sm">
                    Question: <span className="font-medium">"{query}"</span>
                  </p>
                  <p className="text-blue-600 text-xs mt-1">
                    This is a shared search result. You can start a new search using the interface below.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Search Page Content */}
      <SearchPage />

      {/* SEO Meta Tags for Shared Results */}
      {query && (
        <>
          <title>HelpPetAI - {query}</title>
          <meta name="description" content={`Veterinary Q&A: ${query} - Expert answers with trusted sources`} />
          <meta property="og:title" content={`HelpPetAI - ${query}`} />
          <meta property="og:description" content={`Expert veterinary answer for: ${query}`} />
          <meta property="og:type" content="article" />
          <meta property="og:url" content={window.location.href} />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content={`HelpPetAI - ${query}`} />
          <meta name="twitter:description" content={`Expert veterinary answer for: ${query}`} />
        </>
      )}
    </div>
  );
};
