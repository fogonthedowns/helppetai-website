import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Phone, Mic, Calendar, Clock, CheckCircle2, Shield, Zap, ArrowRight } from 'lucide-react';
import Footer from './Footer';

const Home = () => {
  const [callsPerDay, setCallsPerDay] = useState(50);
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
      question: 'What happens if the call requires a human touch or urgent care?',
      answer: 'Every call has a built-in emergency hatch. If a call requires a human touch, it seamlessly transfers to your team with full context of the conversation, ensuring safety, trust, and the best possible experience for pet owners.'
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

  // Calculator logic: calls per day * 80% * 5 minutes * $12/hour rate
  const savedCalls = Math.round(callsPerDay * 0.8);
  const savedMinutesPerDay = savedCalls * 5;
  const savedHoursPerDay = savedMinutesPerDay / 60;
  const hourlyCost = 12;
  const dailySavings = savedHoursPerDay * hourlyCost;
  const monthlySavings = dailySavings * 22; // working days per month
  const annualSavings = monthlySavings * 12;

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-white pt-6 pb-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto text-center">
            {/* Hero Visual - Logo Display */}
            <div className="flex justify-center items-center gap-4 mb-4">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                <Phone className="w-10 h-10 text-blue-600" />
              </div>
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                <Mic className="w-10 h-10 text-green-600" />
              </div>
              <div className="relative">
                <img 
                  src="/logo_clear_back.png" 
                  alt="HelpPetAI" 
                  className="w-32 h-32 object-contain"
                />
              </div>
              <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center">
                <Calendar className="w-10 h-10 text-orange-600" />
              </div>
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-blue-600" />
              </div>
            </div>
            <h1 className="text-7xl font-bold text-gray-900 mb-3 leading-tight tracking-tight" style={{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif',
            }}>
              An AI veterinary voice agent
            </h1>
            <p className="text-2xl text-gray-600 mb-6 max-w-3xl mx-auto leading-relaxed" style={{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
            }}>
              Save 80% of phone time with your AI Front Desk Agent
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                to="/contact" 
                className="bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-medium hover:bg-blue-700 transition-all inline-flex items-center justify-center gap-2"
              >
                Get HelpPetAI free
              </Link>
              <Link 
                to="/contact" 
                className="bg-blue-50 text-blue-700 px-8 py-4 rounded-lg text-lg font-medium hover:bg-blue-100 transition-all inline-flex items-center justify-center gap-2"
              >
                Request a demo
              </Link>
            </div>
          </div>

          {/* Feature Showcase - Dashboard Preview */}
          <div className="mt-10 max-w-6xl mx-auto">
            <div className="bg-gray-50 rounded-2xl border border-gray-200 shadow-2xl overflow-hidden">
              <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <div className="text-sm text-gray-500 font-medium">Call Dashboard</div>
                <div className="w-20"></div>
              </div>
              <div className="p-4 bg-gradient-to-br from-blue-50 via-white to-orange-50">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Phone className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="text-sm font-medium text-gray-600">AI Calls Handled</div>
                    </div>
                    <div className="text-3xl font-bold text-gray-900">247</div>
                    <div className="text-sm text-green-600 mt-1">↑ 80% automated</div>
                  </div>
                  <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-green-600" />
                      </div>
                      <div className="text-sm font-medium text-gray-600">Appointments Booked</div>
                    </div>
                    <div className="text-3xl font-bold text-gray-900">52</div>
                    <div className="text-sm text-green-600 mt-1">This week</div>
                  </div>
                  <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                        <Clock className="w-5 h-5 text-orange-600" />
                      </div>
                      <div className="text-sm font-medium text-gray-600">Time Saved</div>
                    </div>
                    <div className="text-3xl font-bold text-gray-900">18.5h</div>
                    <div className="text-sm text-green-600 mt-1">This week</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Indicators */}
      <section className="bg-white py-4 border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center">
            <p className="text-sm text-gray-500 font-medium mb-3">Stay on top of your practice</p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-60">
              <div className="text-2xl font-bold text-gray-400">Google Calendar</div>
              <div className="text-2xl font-bold text-gray-400">Email Notifications</div>
              <div className="text-2xl font-bold text-gray-400">Text Messages</div>
              <div className="text-2xl font-bold text-gray-400">Push Notifications</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid - Notion Style */}
      <section className="bg-gray-50 py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
            {/* AI Phone Agent */}
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl p-8 text-white min-h-[320px] flex flex-col justify-between hover:shadow-2xl transition-shadow">
              <div>
                <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mb-6">
                  <Phone className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-4xl font-bold mb-4 leading-tight" style={{
                  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
                }}>
                  AI Phone Agent
                </h2>
                <p className="text-blue-100 text-lg leading-relaxed">
                  24/7 call handling, appointment scheduling, and intelligent triage that saves your team 80% of phone time.
                </p>
              </div>
              <Link to="/contact" className="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors inline-flex items-center gap-2 self-start mt-6">
                Learn more →
              </Link>
            </div>

            {/* Voice Documentation */}
            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-3xl p-8 text-white min-h-[320px] flex flex-col justify-between hover:shadow-2xl transition-shadow">
              <div>
                <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mb-6">
                  <Mic className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-4xl font-bold mb-4 leading-tight" style={{
                  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
                }}>
                  Outbound Calls
                </h2>
                <p className="text-green-100 text-lg leading-relaxed">
                  Our agent can make outbound calls to pet owners to remind them about appointments, and handle rescheduling requests.
                </p>
              </div>
              <Link to="/contact" className="bg-white text-green-600 px-6 py-3 rounded-lg font-medium hover:bg-green-50 transition-colors inline-flex items-center gap-2 self-start mt-6">
                Earning your trust →
              </Link>
            </div>

            {/* Smart Calendar */}
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-3xl p-8 text-white min-h-[320px] flex flex-col justify-between hover:shadow-2xl transition-shadow">
              <div>
                <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mb-6">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-4xl font-bold mb-4 leading-tight" style={{
                  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
                }}>
                  Smart Calendar
                </h2>
                <p className="text-orange-100 text-lg leading-relaxed">
                  Intelligent scheduling with practice management integration and automated follow-ups.
                </p>
              </div>
              <Link to="/contact" className="bg-white text-orange-600 px-6 py-3 rounded-lg font-medium hover:bg-orange-50 transition-colors inline-flex items-center gap-2 self-start mt-6">
                Automate scheduling →
              </Link>
            </div>
          </div>

          {/* Feature Pills */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">24/7 Availability</h3>
              </div>
              <p className="text-sm text-gray-600">Always on, never misses a call</p>
            </div>
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="w-5 h-5 text-green-600" />
                <h3 className="font-semibold text-gray-900">Call Recordings</h3>
              </div>
              <p className="text-sm text-gray-600">Know exactly how the phone call went.</p>
            </div>
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-2">
                <Zap className="w-5 h-5 text-orange-600" />
                <h3 className="font-semibold text-gray-900">Instant Setup</h3>
              </div>
              <p className="text-sm text-gray-600">Live in minutes, not weeks</p>
            </div>
            <div className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow">
              <div className="flex items-center gap-3 mb-2">
                <Phone className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Human Handoff</h3>
              </div>
              <p className="text-sm text-gray-600">Seamless transfer anytime</p>
            </div>
          </div>
        </div>
      </section>

      {/* Savings Calculator - Notion Style */}
      <section className="bg-white py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3" style={{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
            }}>
              <span className="whitespace-nowrap">More time</span><br />
              <span className="whitespace-nowrap">with the animals.</span>
            </h2>
            <p className="text-xl text-gray-600">
              Calculate your savings below.
            </p>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-3xl p-8">
            <div className="mb-6">
              <label className="block text-lg font-semibold text-gray-900 mb-6">
                Phone calls per day
              </label>
              <div className="relative">
                <input
                  type="range"
                  min="10"
                  max="200"
                  value={callsPerDay}
                  onChange={(e) => setCallsPerDay(parseInt(e.target.value))}
                  className="w-full h-3 bg-gray-200 rounded-full appearance-none cursor-pointer slider"
                  style={{
                    background: `linear-gradient(to right, #2563eb 0%, #2563eb ${((callsPerDay - 10) / 190) * 100}%, #e5e7eb ${((callsPerDay - 10) / 190) * 100}%, #e5e7eb 100%)`
                  }}
                />
                <div className="flex justify-between mt-4">
                  <span className="text-sm text-gray-500">10</span>
                  <span className="text-2xl font-bold text-blue-600">{callsPerDay}</span>
                  <span className="text-sm text-gray-500">200</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-white rounded-2xl p-5 border border-gray-200">
                <div className="text-sm font-medium text-gray-600 mb-2">Calls Automated</div>
                <div className="text-4xl font-bold text-gray-900 mb-1">{savedCalls}</div>
                <div className="text-sm text-green-600">80% of total calls</div>
              </div>
              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                <div className="text-sm font-medium text-gray-600 mb-2">Monthly Savings</div>
                <div className="text-4xl font-bold text-gray-900 mb-1">${Math.round(monthlySavings)}</div>
                <div className="text-sm text-gray-500">~{Math.round(savedHoursPerDay * 22)}hrs saved/month</div>
              </div>
              <div className="bg-white rounded-2xl p-6 border border-gray-200">
                <div className="text-sm font-medium text-gray-600 mb-2">Annual Savings</div>
                <div className="text-4xl font-bold text-gray-900 mb-1">${Math.round(annualSavings).toLocaleString()}</div>
                <div className="text-sm text-gray-500">At $12/hour rate</div>
              </div>
            </div>

            <div className="text-center">
              <p className="text-sm text-gray-500 mb-4">
                Based on 5 minutes per call, 80% automation rate, and $12/hour staff cost
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-gray-50 py-12 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h2 className="text-4xl font-bold text-gray-900 text-center" style={{
              fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
            }}>
              Frequently asked questions
            </h2>
          </div>
          <div className="bg-white rounded-2xl overflow-hidden border border-gray-200">
            {faqs.map((faq, index) => (
              <div key={index} className="border-b border-gray-100 last:border-b-0">
                <button
                  className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors"
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                >
                  <span className="text-lg font-medium text-black pr-8 leading-relaxed" style={{
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
                  }}>
                    {faq.question}
                  </span>
                  <ArrowRight
                    className={`w-6 h-6 text-gray-400 transition-transform flex-shrink-0 ${
                      expandedFaq === index ? 'rotate-90' : ''
                    }`}
                  />
                </button>
                {expandedFaq === index && (
                  <div className="px-6 pb-6 pt-2 text-gray-600">
                    <p className="text-base leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl font-bold text-white mb-6 leading-tight">
            Save 80% of phone time with<br />
            your AI Front Desk Agent
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join veterinary practices automating calls, scheduling, triage, and documentation with voice-first AI
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Link 
              to="/contact" 
              className="bg-white text-blue-600 px-8 py-4 rounded-lg text-lg font-bold hover:bg-gray-100 transition-colors inline-flex items-center justify-center gap-2"
            >
              Build my Front Desk Agent
            </Link>
            <a 
              href="tel:425-584-1920"
              className="bg-blue-800 text-white px-8 py-4 rounded-lg text-lg font-bold hover:bg-blue-900 transition-colors inline-flex items-center justify-center gap-2"
            >
              <Phone className="w-5 h-5" />
              Try it: 425-584-1920
            </a>
          </div>
          <p className="text-sm text-blue-200">Voice-First Design • Practice Management Integration</p>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Home;