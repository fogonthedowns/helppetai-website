import React from 'react';
import { Check, X } from 'lucide-react';
import { Link } from 'react-router-dom';

const Comparison: React.FC = () => {
  const features = [
    {
      category: "AI Phone Agent",
      items: [
        { feature: "24/7 AI Phone Answering", helppetai: true, petdesk: false },
        { feature: "Natural Voice Conversations", helppetai: true, petdesk: false },
        { feature: "Automated Appointment Scheduling", helppetai: true, petdesk: false },
        { feature: "Phone Call Transcriptions", helppetai: true, petdesk: false },
        { feature: "Reduces Staff Phone Time by 80%", helppetai: true, petdesk: false },
      ]
    },
    {
      category: "Documentation",
      items: [
        { feature: "Visit Call Recordings", helppetai: true, petdesk: false },
        { feature: "AI-Generated Visit Notes", helppetai: true, petdesk: false }      ]
    },
    {
      category: "Pricing & Setup",
      items: [
        { feature: "Transparent Pricing", helppetai: true, petdesk: true },
        { feature: "No Long-term Contracts Required", helppetai: true, petdesk: false },
        { feature: "Quick Setup (< 1 week)", helppetai: true, petdesk: false },
        { feature: "Free Trial Available", helppetai: true, petdesk: true },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-b from-gray-50 to-white py-8 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-2">
            HelpPetAI vs PetDesk
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            See how HelpPetAI's AI-powered phone automation wins over PetDesk customers.
          </p>
        </div>
      </div>

      {/* Main Comparison Table */}
      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Desktop Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-2 px-6 font-semibold text-gray-900 text-lg">Feature</th>
                <th className="text-center py-2 px-6 font-semibold text-gray-900 text-lg">
                  <div className="flex flex-col items-center">
                    <img 
                      src="/logo_clear_back.png" 
                      alt="HelpPetAI" 
                      className="w-12 h-12 mb-1"
                    />
                    <span>HelpPetAI</span>
                  </div>
                </th>
                <th className="text-center py-2 px-6 font-semibold text-gray-900 text-lg">PetDesk</th>
              </tr>
            </thead>
            <tbody>
              {features.map((category, categoryIndex) => (
                <React.Fragment key={categoryIndex}>
                  <tr className="bg-gray-50">
                    <td colSpan={3} className="py-2 px-6 font-bold text-gray-900 text-base">
                      {category.category}
                    </td>
                  </tr>
                  {category.items.map((item, itemIndex) => (
                    <tr key={itemIndex} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="py-2 px-6 text-gray-700">{item.feature}</td>
                      <td className="py-2 px-6 text-center">
                        {item.helppetai ? (
                          <div className="flex justify-center">
                            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                              <Check className="w-5 h-5 text-green-600" />
                            </div>
                          </div>
                        ) : (
                          <div className="flex justify-center">
                            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                              <X className="w-5 h-5 text-gray-400" />
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="py-2 px-6 text-center">
                        {item.petdesk ? (
                          <div className="flex justify-center">
                            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                              <Check className="w-5 h-5 text-green-600" />
                            </div>
                          </div>
                        ) : (
                          <div className="flex justify-center">
                            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                              <X className="w-5 h-5 text-gray-400" />
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile Cards */}
        <div className="md:hidden space-y-4">
          {features.map((category, categoryIndex) => (
            <div key={categoryIndex} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 py-2 px-4 font-bold text-gray-900">
                {category.category}
              </div>
              <div className="divide-y divide-gray-100">
                {category.items.map((item, itemIndex) => (
                  <div key={itemIndex} className="p-3">
                    <div className="font-medium text-gray-900 mb-2">{item.feature}</div>
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-2">
                        <img 
                          src="/logo_clear_back.png" 
                          alt="HelpPetAI" 
                          className="w-6 h-6"
                        />
                        <span className="text-sm text-gray-600">HelpPetAI</span>
                      </div>
                      {item.helppetai ? (
                        <div className="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-green-600" />
                        </div>
                      ) : (
                        <div className="w-7 h-7 bg-gray-100 rounded-full flex items-center justify-center">
                          <X className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-sm text-gray-600">PetDesk</span>
                      {item.petdesk ? (
                        <div className="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-green-600" />
                        </div>
                      ) : (
                        <div className="w-7 h-7 bg-gray-100 rounded-full flex items-center justify-center">
                          <X className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Differentiators */}
      <div className="bg-gray-50 py-8 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-5 text-center">
            Why Choose HelpPetAI?
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Risk Free trial
              </h3>
              <p className="text-gray-600">
                Give it a try for free. We know you'll love it.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Quick Setup
              </h3>
              <p className="text-gray-600">
                Get started in less than a week with our streamlined onboarding process. No complex integrations or lengthy training required.
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Flexible Terms
              </h3>
              <p className="text-gray-600">
                No long-term contracts. Try our service risk-free and scale as your practice grows. Cancel anytime with no penalties.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600 py-8 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
            Ready to save 80% of your phone time?
          </h2>
          <p className="text-xl text-blue-100 mb-5">
            Join veterinary practices already using AI to handle their front desk operations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/contact"
              className="inline-flex items-center justify-center px-8 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition-colors"
            >
              Start Free Trial
            </Link>
            <Link
              to="/about"
              className="inline-flex items-center justify-center px-8 py-3 bg-blue-700 text-white font-semibold rounded-lg hover:bg-blue-800 transition-colors border border-blue-500"
            >
              Learn More
            </Link>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="max-w-6xl mx-auto px-6 py-4">
        <p className="text-sm text-gray-500 text-center">
          * Feature comparison based on publicly available information as of {new Date().getFullYear()}. 
          PetDesk is a registered trademark of PetDesk, Inc. We are not affiliated with PetDesk.
        </p>
      </div>
    </div>
  );
};

export default Comparison;
