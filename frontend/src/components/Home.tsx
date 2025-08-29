import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, Brain, DollarSign, Clock, Stethoscope } from 'lucide-react';
import TransformSection from './TransformSection';

const Home = () => {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const faqs = [
    {
      question: 'How does HelpPetAI determine if my pet needs a vet visit?',
      answer: 'Our Expert AI analyzes symptoms against our veterinary library to provide instant triage recommendations.'
    },
    {
      question: 'What types of conditions can HelpPetAI treat remotely?',
      answer: 'We guide on common issues like digestive upset, skin problems, and behavior. Serious conditions require in-person care.'
    },
    {
      question: 'Are the veterinarians licensed in my state?',
      answer: 'Yes, we connect you with licensed veterinary professionals who meet all local regulatory requirements.'
    },
    {
      question: 'How much money can I actually save?',
      answer: 'Pet owners avoid $200-500+ emergency visits. Practices reduce intake costs and optimize patient time through efficient AI triage.'
    },
    {
      question: 'What happens in emergency situations?',
      answer: 'For life-threatening symptoms, seek emergency veterinary care immediately.'
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - EXACT Wealthfront Style */}
      <section className="bg-gradient-to-br from-pink-50 to-orange-50 w-full py-20">
        <div className="w-full max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="lg:pr-8">
              <h1 className="text-7xl lg:text-8xl font-bold leading-tight mb-8" style={{
                fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                Vet care works better here.
              </h1>
              
              <div className="flex items-center space-x-8 mb-8">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">Save 85% on vet bills*</div>
                    <div className="text-sm text-gray-600">with AI triage and expert routing</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <Brain className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">Expert System</div>
                    <div className="text-sm text-gray-600">from simple to complex</div>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-4">
                <Link to="/vets" className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                  Get started
                </Link>
                
                <Link to="/rag" className="bg-gray-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  Try RAG Search
                </Link>
              </div>
              
              <p className="text-xs text-gray-500">*Rate subject to case complexity</p>
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
                        <div className="text-xs font-medium text-blue-800 mb-1">Patient Info</div>
                        <div className="text-lg font-bold">Golden Retriever • 4 yrs</div>
                        <div className="text-xs text-gray-500">Weight: 28.5 kg | Spayed Female</div>
                      </div>
                      
                      <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Clock className="w-4 h-4 text-orange-600" />
                          <span className="text-xs font-medium text-orange-800">Triage Priority</span>
                        </div>
                        <div className="text-lg font-bold text-orange-700">MODERATE</div>
                        <div className="text-xs text-orange-600">24h observation recommended</div>
                      </div>
                      
                      <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                        <div className="text-xs font-medium text-red-800 mb-1">Primary Symptoms</div>
                        <div className="text-sm font-semibold text-red-700">Emesis • Lethargy</div>
                        <div className="text-xs text-gray-500">Duration: 8 hours • Frequency: 3x</div>
                      </div>
                      
                      <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-xs font-medium text-green-800">Case Status</span>
                        </div>
                        <div className="text-sm font-bold text-green-700">Treatment Plan Active</div>
                        <div className="text-xs text-green-600">DVM consultation scheduled</div>
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
          {/* First Row - Two Large Clean Boxes */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Clean Red Box */}
            <div className="bg-gradient-to-br from-red-400 to-red-500 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  9 ways to improve<br />
                  pet wellness
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
                  Emergency pet<br />
                  care guide
                </h2>
              </div>
              <Link to="/vets" className="bg-white text-orange-600 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Learn more
              </Link>
            </div>
          </div>

          {/* Second Row - Four Clean Condition Boxes */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Skin Allergies</h3>
              <p className="text-purple-100 text-sm font-medium">Better comfort</p>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Ear Infections</h3>
              <p className="text-orange-100 text-sm font-medium">Pain relief</p>
            </div>
            <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Digestive Issues</h3>
              <p className="text-purple-100 text-sm font-medium">Better digestion</p>
            </div>
            <div className="bg-gradient-to-br from-amber-600 to-orange-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <h3 className="text-lg font-light mb-2">Parasite Control</h3>
              <p className="text-orange-100 text-sm font-medium">Protection</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section - Full Width */}
      <section className="bg-blue-600 py-24 w-full">
        <div className="w-full px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-5xl font-bold text-white mb-6 leading-tight">
              Stop overpaying for<br />
              simple pet problems
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join 500,000+ pet parents saving money with smarter vet care
            </p>
            <Link to="/vets" className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-bold hover:bg-gray-100 transition-colors">
              Start free assessment
            </Link>
            <p className="text-sm text-blue-200 mt-4">No subscription required • Licensed vets available 24/7</p>
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
      
    </div>
  );
};

export default Home;
