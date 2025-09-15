import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, DollarSign, Clock, Stethoscope, Phone, Calendar, Mic } from 'lucide-react';
import TransformSection from './TransformSection';
import Footer from './Footer';

const Home = () => {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const faqs = [
    {
      question: 'How does the AI Front Desk Agent handle phone calls?',
      answer: 'Our AI agent answers calls 24/7, handles appointment scheduling, basic triage questions, and routes urgent cases to appropriate staff - all while integrating with your existing practice management system.'
    },
    {
      question: 'Can the system really save 80% of phone time?',
      answer: 'Yes! By automating routine calls, appointment scheduling, prescription refill requests, and basic questions, your staff can focus on patient care instead of phone management.'
    },
    {
      question: 'How does voice recording work during vet visits?',
      answer: 'Simply open the HelpPet.ai app on your iPhone and start recording. The AI automatically transcribes the conversation, extracts key medical information, and integrates with your practice records.'
    },
    {
      question: 'Is the AI Front Desk Agent secure and compliant?',
      answer: 'Absolutely. All voice data is encrypted and transmitted to secure cloud storage. Only authorized practice staff have access to patient information.'
    },
    {
      question: 'Does it integrate with existing calendar systems?',
      answer: 'Yes, our calendar automation works with major practice management systems to automatically schedule appointments, send reminders, and manage follow-up care based on AI-analyzed visit notes.'
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
                Meet LaShonda
                An AI veterinary voice agent with serious front desk skills
              </h1>

              <p className="text-2xl text-gray-600 mb-8 font-light">
                Save 80% of phone time with intelligent check-in, triage, and voice-powered documentation.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <Phone className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">AI Phone Agent</div>
                    <div className="text-sm text-gray-600">24/7 calls, scheduling & triage</div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                    <Mic className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">Voice Documentation</div>
                    <div className="text-sm text-gray-600">iPhone recording & transcription</div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">Smart Check-In</div>
                    <div className="text-sm text-gray-600">AI-powered patient triage</div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">Calendar Automation</div>
                    <div className="text-sm text-gray-600">Smart scheduling & follow-ups</div>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-4">
                <Link to="/vets" className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2">
                  <ArrowRight className="w-4 h-4" />
                  Start AI Front Desk
                </Link>

                <a href="tel:425-584-1920" className="bg-gray-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors flex items-center gap-2">
                  <Phone className="w-4 h-4" />
                  Try it: 425-584-1920
                </a>
              </div>

              <p className="text-xs text-gray-500">Voice-First Design • Practice Management Integration</p>
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
                        <div className="flex items-center space-x-2 mb-2">
                          <Phone className="w-4 h-4 text-blue-600" />
                          <span className="text-xs font-medium text-blue-800">AI Phone Agent</span>
                        </div>
                        <div className="text-lg font-bold text-blue-700">HANDLING CALL</div>
                        <div className="text-xs text-blue-600">"Scheduling Bella for checkup..."</div>
                      </div>

                      <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Mic className="w-4 h-4 text-green-600" />
                          <span className="text-xs font-medium text-green-800">Voice Recording</span>
                        </div>
                        <div className="text-lg font-bold">Amira • Golden Retriever</div>
                        <div className="text-xs text-gray-500">Visit Recording • Auto-transcribing</div>
                      </div>

                      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <CheckCircle className="w-4 h-4 text-purple-600" />
                          <span className="text-xs font-medium text-purple-800">Smart Triage</span>
                        </div>
                        <div className="text-sm font-semibold text-purple-700">Urgent - GDV symptoms</div>
                        <div className="text-xs text-purple-600">Prioritized & Dr. alerted</div>
                      </div>

                      <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Calendar className="w-4 h-4 text-orange-600" />
                          <span className="text-xs font-medium text-orange-800">Auto-Scheduling</span>
                        </div>
                        <div className="text-sm font-bold text-orange-700">3 appointments booked</div>
                        <div className="text-xs text-orange-600">Follow-ups scheduled</div>
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
            {/* AI Phone Agent Box */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  AI Phone Agent<br />
                  24/7 Support
                </h2>
                <p className="text-blue-100 text-lg">Handles calls, scheduling, and triage automatically</p>
              </div>
              <Link to="/vets" className="bg-white text-blue-600 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Start AI Agent
              </Link>
            </div>

            {/* Voice Documentation Box */}
            <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  Voice-Powered<br />
                  Documentation
                </h2>
                <p className="text-green-100 text-lg">iPhone recording with AI transcription & analysis</p>
              </div>
              <Link to="/vets" className="bg-white text-green-600 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Try Recording
              </Link>
            </div>

            {/* Smart Calendar Box */}
            <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-3xl p-12 text-white relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-4xl font-light leading-tight mb-4" style={{
                  fontFamily: 'Calibre, ui-sans-serif, system-ui, -apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif'
                }}>
                  Smart Calendar<br />
                  Automation
                </h2>
                <p className="text-orange-100 text-lg">Intelligent scheduling with practice management integration</p>
              </div>
              <Link to="/vets" className="bg-white text-orange-600 px-6 py-3 rounded-full font-medium text-sm hover:bg-gray-100 transition-colors self-start">
                Automate Scheduling
              </Link>
            </div>
          </div>

          {/* Second Row - Four Key Features */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <div className="flex items-center mb-3">
                <Phone className="w-6 h-6 mr-2" />
                <h3 className="text-lg font-light">Phone Automation</h3>
              </div>
              <p className="text-blue-100 text-sm font-medium">80% less call time</p>
            </div>
            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <div className="flex items-center mb-3">
                <Mic className="w-6 h-6 mr-2" />
                <h3 className="text-lg font-light">Voice Recording</h3>
              </div>
              <p className="text-green-100 text-sm font-medium">iPhone to cloud</p>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <div className="flex items-center mb-3">
                <CheckCircle className="w-6 h-6 mr-2" />
                <h3 className="text-lg font-light">Smart Triage</h3>
              </div>
              <p className="text-purple-100 text-sm font-medium">AI-powered priority</p>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-8 text-white hover:scale-105 transition-transform cursor-pointer">
              <div className="flex items-center mb-3">
                <Calendar className="w-6 h-6 mr-2" />
                <h3 className="text-lg font-light">Auto-Scheduling</h3>
              </div>
              <p className="text-orange-100 text-sm font-medium">Calendar integration</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section - Full Width */}
      <section className="bg-blue-600 py-24 w-full">
        <div className="w-full px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-5xl font-bold text-white mb-6 leading-tight">
              Save 80% of phone time with<br />
              your AI Front Desk Agent
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join veterinary practices automating calls, scheduling, triage, and documentation with voice-first AI
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
              <Link to="/vets" className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-bold hover:bg-gray-100 transition-colors flex items-center gap-2">
                <ArrowRight className="w-5 h-5" />
                Start AI Front Desk
              </Link>
              <a href="tel:425-584-1920" className="bg-blue-800 text-white px-8 py-4 rounded-lg text-lg font-bold hover:bg-blue-900 transition-colors flex items-center gap-2">
                <Phone className="w-5 h-5" />
                Try it: 425-584-1920
              </a>
            </div>
            <p className="text-sm text-blue-200">Voice-First Design • Practice Management Integration</p>
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
