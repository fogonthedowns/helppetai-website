import React from 'react';
import { Link } from 'react-router-dom';
import { Globe, Zap, Shield, DollarSign, CheckCircle } from 'lucide-react';

const WebsiteHosting: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - Notion Style */}
      <div className="max-w-5xl mx-auto px-6 py-16">
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-gray-100 text-gray-600 text-sm font-medium rounded-full">
            Website Hosting
          </span>
        </div>
        
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Professional websites made simple
        </h1>
        
        <p className="text-xl text-gray-600 mb-8 max-w-3xl">
          Fast, secure hosting for your veterinary practice. Choose from professional templates, get online in minutes, and focus on what matters most - your patients.
        </p>
        
        <div className="flex gap-4 mb-16">
          <Link 
            to="/signup" 
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Get started for $7/month
          </Link>
          <Link 
            to="/contact" 
            className="bg-gray-100 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            View templates →
          </Link>
        </div>

        {/* Feature Highlights */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Zap className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Blazing Fast</h3>
              <p className="text-sm text-gray-600">Global CDN ensures your site loads in under 2 seconds worldwide.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Zero Maintenance</h3>
              <p className="text-sm text-gray-600">We handle updates, security, and backups. You focus on your practice.</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <DollarSign className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">Extreme Value</h3>
              <p className="text-sm text-gray-600">Starting at $7/month. No setup fees, no hidden costs.</p>
            </div>
          </div>
        </div>

        {/* Templates Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Professional templates</h2>
          <p className="text-lg text-gray-600 mb-8">
            Choose from modern, classic, minimal, and professional designs crafted specifically for veterinary practices.
          </p>
          
          <div className="bg-gray-50 rounded-lg p-8">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">What's included:</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-gray-700">Mobile-optimized responsive design</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-gray-700">Online appointment booking integration</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-gray-700">Team profiles and service pages</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-gray-700">Contact forms and location maps</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-gray-700">SEO optimization for local search</span>
                  </div>
                </div>
              </div>
              
              <div className="text-center">
                <img 
                  src="/logo_clear_back.png" 
                  alt="HelpPetAI" 
                  className="w-32 h-32 mx-auto mb-4"
                />
                <p className="text-gray-600">6 professional templates available</p>
              </div>
            </div>
          </div>
        </div>

        {/* Pricing Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Simple pricing</h2>
          <p className="text-lg text-gray-600 mb-8">
            No setup fees, no hidden costs, cancel anytime.
          </p>
          
          <div className="bg-white border border-gray-200 rounded-lg p-8 max-w-md">
            <div className="text-center mb-6">
              <div className="text-4xl font-bold text-gray-900 mb-2">$7</div>
              <div className="text-gray-600">per month</div>
            </div>
            
            <div className="space-y-3 mb-8">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">Professional veterinary template</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">99.9% uptime guarantee</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">SSL certificate included</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">Custom domain name</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-gray-700">24/7 technical support</span>
              </div>
            </div>
            
            <Link 
              to="/signup" 
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors text-center block"
            >
              Get started today
            </Link>
          </div>
        </div>

        {/* Technical Details */}
        <div className="border-t border-gray-200 pt-16">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Built for veterinary practices</h2>
          
          <div className="grid md:grid-cols-2 gap-12">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Performance</h3>
              <div className="space-y-3 text-gray-600">
                <p>• Global CDN with edge caching</p>
                <p>• 99.9% uptime SLA guarantee</p>
                <p>• Automatic scaling for traffic spikes</p>
                <p>• Mobile-first responsive design</p>
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Security & Maintenance</h3>
              <div className="space-y-3 text-gray-600">
                <p>• Free SSL certificates with auto-renewal</p>
                <p>• Security monitoring and malware scanning</p>
                <p>• Automatic updates and patches</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebsiteHosting;