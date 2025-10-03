import React from 'react';
import { Link } from 'react-router-dom';
import { Phone, Calendar, MessageSquare, Clock, CheckCircle, Users } from 'lucide-react';

const AIFrontDesk: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - Notion Style */}
      <div className="max-w-5xl mx-auto px-6 py-16">
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-gray-100 text-gray-600 text-sm font-medium rounded-full">
            AI Front Desk
          </span>
        </div>
        
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          The next generation of veterinary front desk
        </h1>
        
        <p className="text-xl text-gray-600 mb-8 max-w-3xl">
          Simple. Powerful. Beautiful. Handle more calls efficiently with our AI-powered phone agent that eliminates hold times, stays consistently friendly, and provides excellent service every time.
        </p>
        
        <div className="flex gap-4 mb-16">
          <Link 
            to="/signup" 
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Try AI Front Desk free
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
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Phone className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">24/7 Availability</h3>
              <p className="text-sm text-gray-600">Answer calls around the clock, even after hours and on weekends.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Calendar className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Smart Scheduling</h3>
              <p className="text-sm text-gray-600">Book appointments automatically with real-time calendar integration.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <MessageSquare className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Natural Conversations</h3>
              <p className="text-sm text-gray-600">AI that understands context and provides helpful, accurate responses.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Use Cases Section */}
      <div className="bg-gray-50 py-16">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-3 text-center">
            Built for every role in your practice
          </h2>
          <p className="text-lg text-gray-600 mb-12 text-center">
            See how our AI Front Desk transforms daily operations for your entire team.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Receptionist */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <Phone className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Receptionist</h3>
              <p className="text-gray-600 mb-4">
                Free up your front desk staff from repetitive phone calls. Let them focus on in-person patient care while AI handles routine scheduling and questions.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Handle multiple calls simultaneously</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Reduce hold times to zero</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Escape hatch for human intervention</span>
                </li>
              </ul>
            </div>

            {/* Appointment Setter */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <Calendar className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Appointment Setter</h3>
              <p className="text-gray-600 mb-4">
                Book more appointments without lifting a finger. Our AI checks availability, suggests optimal times, and confirms bookings instantly.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Real-time calendar synchronization</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Smart conflict detection</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Automatic reminders and follow-ups</span>
                </li>
              </ul>
            </div>

              {/* Basic Inquiries */}
              <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Users className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Basic Inquiries</h3>
                <p className="text-gray-600 mb-4">
                  Answer routine questions instantly without tying up your staff. Handle everything from clinic hours to prescription refills with accurate, consistent information.
                </p>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">Office hours and location details</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">Medication refill status and pickup times</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-gray-700">Vaccine protocols and wellness exam schedules</span>
                  </li>
                </ul>
              </div>

            {/* After-Hours Coverage */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">After-Hours Coverage</h3>
              <p className="text-gray-600 mb-4">
                Never miss a call or potential client. Provide 24/7 service without paying for overnight staff or answering services.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Weekend and holiday coverage</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Emergency call forwarding</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">Instant staff notifications for urgent cases</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to transform your front desk?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join hundreds of veterinary practices saving 80% of phone time with AI.
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

export default AIFrontDesk;

