import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, Brain, DollarSign, Clock, Stethoscope } from 'lucide-react';
import TransformSection from './TransformSection';
import Footer from './Footer';

const Home = () => {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const faqs = [
    {
      question: 'How does iPhone recording work during vet visits?',
      answer: 'Simply open the HelpPet.ai app on your iPhone, select the pet, and start recording. Audio uploads directly to secure cloud storage with automatic transcription.'
    },
    {
      question: 'Is the recorded audio secure and SOC 2 Type 2 compliant?',
      answer: 'Yes, all recordings use encrypted transmission to AWS S3 with role-based access controls. Only authorized veterinary staff and pet owners can access visit records.'
    },
    {
      question: 'Can multiple veterinary practices access the same pet records?',
      answer: 'Yes, pet owners can connect with multiple practices (primary care, specialists, emergency clinics) to share complete medical histories and visit transcripts.'
    },
    {
      question: 'How does the AI transcription help with documentation?',
      answer: 'AI automatically converts visit recordings into searchable text transcripts, reducing manual note-taking and ensuring complete visit documentation for compliance.'
    },
    {
      question: 'What happens to the visit recordings and transcripts?',
      answer: 'All recordings and transcripts are stored securely and become part of the permanent medical record, accessible to authorized users across connected practices.'
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - EXACT Wealthfront Style */}
      <section className="bg-gradient-to-br from-pink-50 to-orange-50 w-full py-20">
        <div className="w-full max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="lg:pr-8">
              <h1 className="text-6xl lg:text-7xl font-bold leading-tight mb-8" style={{
                fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Streamline vet visit documentation.
              </h1>
              
              <div className="flex items-center space-x-8 mb-8">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <Stethoscope className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">iPhone Recording</div>
                    <div className="text-sm text-gray-600">Direct cloud upload & transcription</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <Brain className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">AI Documentation</div>
                    <div className="text-sm text-gray-600">Automated transcripts & compliance</div>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-4">
                <Link to="/vets" className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                  Get started
                </Link>
                
                <Link to="/rag" className="bg-gray-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  Veterinary Knowledge Search
                </Link>
              </div>
              
              <p className="text-xs text-gray-500">Secure, SOC-compliant documentation platform</p>
            </div>
            {/* Phone Mockup - Exact Wealthfront Style */}
            <div className="flex justify-center lg:justify-end">
              <div className="relative">
                <div className="w-80 h-[600px] bg-gray-900 rounded-[3rem] p-3 shadow-2xl">
                  <div className="w-full h-full bg-white rounded-[2.5rem] overflow-hidden">
                    {/* Phone Header */}
                    <div className="bg-gray-50 px-6 py-4 border-b border-gray-100">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                          <Stethoscope className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-lg">HelpPetAI</span>
                      </div>
                    </div>
                    
                    {/* Phone Content */}
                    <div className="p-6 space-y-4">
                      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                        <div className="text-xs font-medium text-blue-800 mb-1">Recording Session</div>
                        <div className="text-lg font-bold">Amira • Golden Retriever</div>
                        <div className="text-xs text-gray-500">Visit: Annual Wellness • Dr. Smith</div>
                      </div>
                      
                      <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Clock className="w-4 h-4 text-orange-600" />
                          <span className="text-xs font-medium text-orange-800">Recording Status</span>
                        </div>
                        <div className="text-lg font-bold text-orange-700">ACTIVE</div>
                        <div className="text-xs text-orange-600">12:34 duration • Auto-uploading</div>
                      </div>
                      
                      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                        <div className="text-xs font-medium text-purple-800 mb-1">AI Transcription</div>
                        <div className="text-sm font-semibold text-purple-700">Processing...</div>
                        <div className="text-xs text-gray-500">Converting speech to text</div>
                      </div>
                      
                      <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-xs font-medium text-green-800">Documentation</span>
                        </div>
                        <div className="text-sm font-bold text-green-700">Auto-saved</div>
                        <div className="text-xs text-green-600">Shared across practices</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust indicators - Full Width */}
      <TransformSection />

      {/* Clean Hims-Style Boxes */}
      <section className="w-full bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-6">
          {/* First Row - Three Large Clean Boxes */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {/* Clean Red Box */}
            <div className="bg-gradient-to-br from-red-400 to-red-500 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  iPhone recording<br />
                  made simple
                </h2>
              </div>
              <Link to="/vets" className="bg-white text-red-500 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Explore
              </Link>
            </div>

            {/* Clean Orange Box */}
            <div className="bg-gradient-to-br from-amber-600 to-orange-700 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  AI transcription<br />
                  & compliance
                </h2>
              </div>
              <Link to="/vets" className="bg-white text-orange-600 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Learn more
              </Link>
            </div>

            {/* Clean Blue Box - Practices */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  Multi-practice<br />
                  record sharing
                </h2>
              </div>
              <Link to="/practices" className="bg-white text-blue-600 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Browse practices
              </Link>
            </div>
          </div>

          {/* Second Row - Four Clean Condition Boxes */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Visit Recording</h3>
              <p className="text-purple-100 text-sm font-medium">iPhone to cloud</p>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Auto Transcription</h3>
              <p className="text-orange-100 text-sm font-medium">AI-powered text</p>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Record Management</h3>
              <p className="text-purple-100 text-sm font-medium">Cross-practice sharing</p>
            </div>
            <div className="bg-gradient-to-br from-amber-600 to-orange-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Compliance Ready</h3>
              <p className="text-orange-100 text-sm font-medium">SOC 2 Type 2 secure</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section - Full Width */}
      <section className="bg-blue-600 py-24 w-full">
        <div className="w-full px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-5xl font-bold text-white mb-6 leading-tight">
              Transform your vet visit<br />
              documentation workflow
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join veterinary practices streamlining documentation with iPhone recording and AI transcription
            </p>
            <Link to="/vets" className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-bold hover:bg-gray-100 transition-colors">
              Start documenting visits
            </Link>
            <p className="text-sm text-blue-200 mt-4">SOC 2 Type 2 compliant • Secure cloud storage • Multi-practice sharing</p>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-gray-50 py-24">
        <div className="max-w-4xl mx-auto px-6">
          <div className="mb-12">
            <h2 className="text-4xl font-bold text-gray-900 text-center" style={{
              fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
            }}>
              Frequently asked questions
            </h2>
          </div>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            {faqs.map((faq, index) => (
              <div key={index} className="border-b border-gray-100 last:border-b-0">
                <button
                  className="w-full flex items-center justify-between p-10 text-left hover:bg-gray-50 transition-colors"
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                >
                  <span className="text-2xl font-medium text-black pr-8 leading-relaxed" style={{
                    fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                  }}>
                    {faq.question}
                  </span>
                  <ArrowRight
                    className={`w-7 h-7 text-gray-400 transition-transform flex-shrink-0 ${
                      expandedFaq === index ? 'rotate-90' : ''
                    }`}
                  />
                </button>
                {expandedFaq === index && (
                  <div className="px-10 pb-10 pt-2 text-gray-600">
                    <p className="text-lg leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
      
      <Footer />
    </div>
  );
};

export default Home;
