import React from 'react';
import { Check } from 'lucide-react';

const Pricing: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <div className="py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl font-semibold text-gray-900 mb-2">
            Simple, transparent pricing
          </h1>
        </div>
      </div>

      {/* Pay-as-you-go and Add-ons Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        <div className="mb-8">
          <h2 className="text-xl font-medium text-gray-900 mb-4 border-l-4 border-gray-900 pl-3">
            Pay-as-you-go
          </h2>

          {/* Voice AI */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Voice AI calls
              </h3>
              <p className="text-sm text-gray-600">
                AI-powered phone agent that handles appointment scheduling, answers questions, and manages your front desk automatically.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-gray-900">20¢</div>
              <div className="text-sm text-gray-500">per minute</div>
            </div>
          </div>

          {/* Voice Recording */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Visit recording & transcription
              </h3>
              <p className="text-sm text-gray-600">
                Record and transcribe veterinary visits with AI-powered summaries for accurate documentation and record keeping.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-gray-900">25¢</div>
              <div className="text-sm text-gray-500">per recording</div>
            </div>
          </div>
        </div>

        {/* Add-ons Section */}
        <div className="mb-8">
          <h2 className="text-xl font-medium text-gray-900 mb-4 border-l-4 border-gray-900 pl-3">
            Add-ons
          </h2>

          {/* Phone Number */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Phone number
              </h3>
              <p className="text-sm text-gray-600">
                Dedicated phone number for your practice with unlimited inbound calls.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-gray-900">$10</div>
              <div className="text-sm text-gray-500">per month</div>
            </div>
          </div>

          {/* Toll-free Number */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Toll-free number
              </h3>
              <p className="text-sm text-gray-600">
                Toll-free phone number (1-800) for a professional presence with nationwide coverage.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-gray-900">$15</div>
              <div className="text-sm text-gray-500">per month</div>
            </div>
          </div>

          {/* Website Hosting */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Website hosting
              </h3>
              <p className="text-sm text-gray-600">
                Fast, secure hosting for your practice website with 99.9% uptime guarantee.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-gray-900">$7</div>
              <div className="text-sm text-gray-500">per month</div>
            </div>
          </div>
        </div>

        {/* No Cost Section */}
        <div className="mb-8">
          <h2 className="text-xl font-medium text-gray-900 mb-4 border-l-4 border-green-600 pl-3">
            No Cost
          </h2>

          {/* Appointment Email Notifications */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Appointment email notifications
              </h3>
              <p className="text-sm text-gray-600">
                Automatic email confirmations sent to pet owners with appointment details and calendar attachments.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-green-600">Free</div>
              <div className="text-sm text-gray-500">included</div>
            </div>
          </div>

          {/* Unlimited Seats */}
          <div className="flex items-start justify-between py-4 border-b border-gray-200">
            <div className="flex-1 pr-8">
              <h3 className="font-medium text-gray-900 mb-1">
                Unlimited seats
              </h3>
              <p className="text-sm text-gray-600">
                Add unlimited staff members to your practice account at no additional cost.
              </p>
            </div>
            <div className="text-right flex-shrink-0 w-32">
              <div className="text-lg font-semibold text-green-600">Free</div>
              <div className="text-sm text-gray-500">included</div>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Pricing */}
      <div className="bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-xl font-medium text-gray-900 mb-2 border-l-4 border-gray-900 pl-3">
            Custom pricing
          </h2>
          <p className="text-sm text-gray-600 pl-3">
            If you have high volume needs or unique requirements, reach out to discuss custom pricing options.
          </p>
          <a href="/contact" className="inline-block mt-3 ml-3 text-sm text-blue-600 hover:text-blue-700 font-medium">
            Contact sales →
          </a>
        </div>
      </div>


      {/* CTA Section */}
      <div className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to save 80% of phone time?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join hundreds of veterinary practices using HelpPetAI
          </p>
          <div className="flex gap-4 justify-center">
            <a href="/signup" className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors">
              Start Free Trial
            </a>
            <a href="/contact" className="bg-white text-gray-900 px-8 py-3 rounded-lg font-medium border-2 border-gray-300 hover:border-gray-400 transition-colors">
              Request Demo
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pricing;

