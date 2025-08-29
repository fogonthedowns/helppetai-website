import React, { useState, useEffect, useMemo } from 'react';
import { Copy, Share2, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { RAGResponse } from '../../types/rag';
import { CitationBubble } from '../shared/CitationBubble';
import { parseCitations, copyToClipboard, generateShareableURL, cleanupDuplicateCitations } from '../../utils/searchUtils';

interface AnswerDisplayProps {
  result: RAGResponse;
  searchId?: string;
  onCitationClick?: (sourceIndex: number) => void;
  onCitationHover?: (sourceIndex: number | null) => void;
  className?: string;
}

interface TypewriterTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

const TypewriterText: React.FC<TypewriterTextProps> = ({ 
  text, 
  speed = 0, 
  onComplete 
}) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    // Show text instantly
    setDisplayedText(text);
    if (onComplete) {
      onComplete();
    }
  }, [text, onComplete]);

  return <span>{displayedText}</span>;
};

const FOLLOW_UP_SUGGESTIONS = [
  "What are the treatment options for this condition?",
  "How can I prevent this in the future?",
  "When should I contact a veterinarian?",
  "Are there any breed-specific considerations?",
];

export const AnswerDisplay: React.FC<AnswerDisplayProps> = ({
  result,
  searchId,
  onCitationClick,
  onCitationHover,
  className = "",
}) => {
  const [typewriterComplete, setTypewriterComplete] = useState(false);
  const [copiedText, setCopiedText] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);

  // Clean up and parse citations from the answer (limit to available sources)
  const cleanedAnswer = useMemo(() => cleanupDuplicateCitations(result.answer, result.sources.length), [result.answer, result.sources.length]);
  const citations = useMemo(() => parseCitations(cleanedAnswer, result.sources.length), [cleanedAnswer, result.sources.length]);

  // Replace citations with CitationBubble components
  const renderAnswerWithCitations = (text: string) => {
    if (citations.length === 0) {
      return text;
    }

    const parts = [];
    let lastIndex = 0;

    citations.forEach((citation, index) => {
      // Add text before citation
      if (citation.start > lastIndex) {
        parts.push(text.slice(lastIndex, citation.start));
      }

      // Add citation bubble
      const source = result.sources[citation.sourceIndex];
      parts.push(
        <CitationBubble
          key={`citation-${index}`}
          number={citation.number}
          source={source}
          onClick={() => onCitationClick?.(citation.sourceIndex)}
          onHover={(isHovering) => onCitationHover?.(isHovering ? citation.sourceIndex : null)}
        />
      );

      lastIndex = citation.end;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts;
  };

  const handleCopyAnswer = async () => {
    const success = await copyToClipboard(cleanedAnswer);
    if (success) {
      setCopiedText(true);
      setTimeout(() => setCopiedText(false), 2000);
    }
  };

  const handleShare = async () => {
    if (searchId) {
      const shareUrl = generateShareableURL(searchId, result.query_metadata.question);
      const success = await copyToClipboard(shareUrl);
      if (success) {
        setCopiedUrl(true);
        setTimeout(() => setCopiedUrl(false), 2000);
      }
    }
  };

  const processingTime = result.query_metadata.processing_time_seconds;
  const sourceCount = result.query_metadata.sources_count;

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>
              {sourceCount} source{sourceCount !== 1 ? 's' : ''} found
            </span>
            <span>•</span>
            <span>
              {processingTime.toFixed(1)}s response time
            </span>
            {result.query_metadata.filters_applied && (
              <>
                <span>•</span>
                <span className="text-blue-600">Filtered</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Copy Button */}
            <button
              onClick={handleCopyAnswer}
              className="
                flex items-center gap-2 px-3 py-1.5 text-sm font-medium
                text-gray-600 hover:text-gray-800 hover:bg-gray-100
                rounded-lg transition-colors
              "
              title="Copy answer"
            >
              {copiedText ? (
                <>
                  <Check className="w-4 h-4 text-green-600" />
                  <span className="text-green-600">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>Copy</span>
                </>
              )}
            </button>

            {/* Share Button */}
            {searchId && (
              <button
                onClick={handleShare}
                className="
                  flex items-center gap-2 px-3 py-1.5 text-sm font-medium
                  text-gray-600 hover:text-gray-800 hover:bg-gray-100
                  rounded-lg transition-colors
                "
                title="Share result"
              >
                {copiedUrl ? (
                  <>
                    <Check className="w-4 h-4 text-green-600" />
                    <span className="text-green-600">Copied!</span>
                  </>
                ) : (
                  <>
                    <Share2 className="w-4 h-4" />
                    <span>Share</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Answer Content */}
      <div className="px-6 py-6">
        <div className="prose prose-lg max-w-none">
          <div className="text-gray-800 leading-relaxed">
            {typewriterComplete ? (
              <ReactMarkdown
                components={{
                  // Custom renderer for paragraphs to handle citations
                  p: ({ children, ...props }) => {
                    if (typeof children === 'string') {
                      return <p className="mb-4 text-lg leading-relaxed" {...props}>{renderAnswerWithCitations(children)}</p>;
                    }
                    // Handle mixed content (string + JSX)
                    const processedChildren = React.Children.map(children, (child) => {
                      if (typeof child === 'string') {
                        return renderAnswerWithCitations(child);
                      }
                      return child;
                    });
                    return <p className="mb-4 text-lg leading-relaxed" {...props}>{processedChildren}</p>;
                  },
                  // Style headers
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-gray-900">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 text-gray-900">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-medium mb-2 text-gray-900">{children}</h3>,
                  // Style lists
                  ul: ({ children }) => <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 space-y-2">{children}</ol>,
                  li: ({ children }) => <li className="text-gray-800 text-lg leading-relaxed">{children}</li>,
                  // Style strong/bold text
                  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                  // Style emphasis/italic text
                  em: ({ children }) => <em className="italic text-gray-800">{children}</em>,
                  // Style code
                  code: ({ children }) => <code className="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800">{children}</code>,
                  // Style blockquotes
                  blockquote: ({ children }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700 my-4 bg-blue-50 py-2 rounded-r">{children}</blockquote>,
                }}
              >
                {cleanedAnswer}
              </ReactMarkdown>
            ) : (
              <TypewriterText
                text={cleanedAnswer}
                speed={20}
                onComplete={() => setTypewriterComplete(true)}
              />
            )}
          </div>
        </div>

        {/* Typing indicator */}
        {!typewriterComplete && (
          <div className="inline-flex items-center gap-1 mt-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
        )}
      </div>

      {/* Follow-up Suggestions */}
      {typewriterComplete && (
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Follow-up questions:</h4>
          <div className="flex flex-wrap gap-2">
            {FOLLOW_UP_SUGGESTIONS.map((suggestion, index) => (
              <button
                key={index}
                className="
                  px-3 py-2 text-sm text-gray-600 hover:text-gray-800
                  bg-white hover:bg-gray-100 border border-gray-200 hover:border-gray-300
                  rounded-lg transition-colors
                "
                onClick={() => {
                  // This would trigger a new search with the suggestion
                  console.log('Follow-up search:', suggestion);
                }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
