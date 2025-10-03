import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Mic, Brain, Clock, CheckCircle, Stethoscope, Activity, FileCheck } from 'lucide-react';

const VisitTranscriptions: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - Notion Style */}
      <div className="max-w-5xl mx-auto px-6 py-16">
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-gray-100 text-gray-600 text-sm font-medium rounded-full">
            Visit Transcriptions
          </span>
        </div>
        
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          SOAP notes that write themselves
        </h1>
        
        <p className="text-xl text-gray-600 mb-8 max-w-3xl">
          Record entire veterinary visits and automatically generate comprehensive SOAP notes with AI-powered extraction of symptoms, diagnoses, and treatment plans. The only solution with complete end-to-end context from initial phone call to post-visit follow-up.
        </p>
        
        <div className="flex gap-4 mb-16">
          <Link 
            to="/signup" 
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Try Visit Transcriptions free
          </Link>
          <Link 
            to="/contact" 
            className="bg-gray-100 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            Request a demo →
          </Link>
        </div>

        {/* Feature Highlights */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Mic className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Complete Audio Recording</h3>
              <p className="text-sm text-gray-600">Capture every word from exam room conversations with crystal-clear audio.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Brain className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">AI-Powered SOAP Notes</h3>
              <p className="text-sm text-gray-600">Automatically extract subjective, objective, assessment, and plan from conversations.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Activity className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">End-to-End Context</h3>
              <p className="text-sm text-gray-600">Integrate with inbound call data for complete patient journey documentation.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Unique Advantage Section */}
      <div className="bg-blue-50 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              What makes us better
            </h2>
            <p className="text-lg text-gray-600">
              We're the only solution that captures the complete patient story
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">1</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Inbound Call</h3>
              <p className="text-sm text-gray-600">Client calls with concerns, our AI captures symptoms and chief complaint during scheduling</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">2</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Exam Room Visit</h3>
              <p className="text-sm text-gray-600">Record full conversation, physical exam findings, and treatment discussion with pet owner</p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-white">3</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Complete Record</h3>
              <p className="text-sm text-gray-600">AI synthesizes all touchpoints into comprehensive SOAP notes with full context</p>
            </div>
          </div>

          <div className="mt-12 bg-white rounded-xl p-6 border border-blue-200">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <CheckCircle className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Why end-to-end context matters</h4>
                <p className="text-gray-700">
                  Other solutions only capture what happens in the exam room. We integrate the initial phone conversation, giving you a complete picture of the patient's condition from first contact to diagnosis. This means better documentation, fewer missed details, and more accurate medical records.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Section */}
      <div className="bg-white py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-3 text-center">
            Built for how veterinarians actually work
          </h2>
          <p className="text-lg text-gray-600 mb-12 text-center">
            Save hours on documentation while improving record quality and compliance.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="space-y-8">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Complete SOAP Notes in Minutes</h3>
                    <p className="text-gray-600">
                      Focus on patient care, not paperwork. Record your exam and let AI handle the documentation while you concentrate on diagnosis and treatment.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <FileCheck className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Automatic Clinical Extraction</h3>
                    <p className="text-gray-600">
                      AI automatically extracts subjective, objective, assessment, and plan details from your conversations. Complete conversation archives with searchable medical record history.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Clock className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">80% Reduction in Documentation Time</h3>
                    <p className="text-gray-600">
                      See more patients without sacrificing quality. No more staying late to finish charts. Increase your daily appointment capacity and improve work-life balance.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <FileText className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Automated Client Communication</h3>
                    <p className="text-gray-600">
                      Provide detailed visit summaries and discharge instructions automatically. Clear medication schedules and follow-up care reminders improve client satisfaction.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-center">
              <div className="w-80 h-80 bg-gradient-to-br from-gray-100 to-gray-200 rounded-3xl flex items-center justify-center p-8">
                <img 
                  src="/logo_clear_back.png" 
                  alt="HelpPetAI" 
                  className="w-64 h-64 object-contain"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-gray-50">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to revolutionize your medical records?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join practices saving hours daily on documentation with AI-powered SOAP notes.
          </p>
          <div className="flex gap-4 justify-center">
            <Link 
              to="/signup" 
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Start Free Trial
            </Link>
            <Link 
              to="/pricing" 
              className="bg-white text-gray-900 px-8 py-3 rounded-lg font-medium border-2 border-gray-300 hover:border-gray-400 transition-colors"
            >
              View Pricing
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisitTranscriptions;

