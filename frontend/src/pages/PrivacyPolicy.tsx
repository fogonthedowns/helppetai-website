import React from 'react';
import { Shield, Lock, Eye, FileText, Users, Globe } from 'lucide-react';

const PrivacyPolicy: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <Shield className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Privacy Policy</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Your privacy is important to us. This policy explains how HelpPetAI collects, uses, and protects your information.
          </p>
          <p className="text-sm text-gray-500 mt-4">Last updated: {new Date().toLocaleDateString()}</p>
        </div>

        {/* Privacy Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-blue-50 rounded-lg p-6 text-center">
            <Lock className="w-8 h-8 text-blue-600 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">Secure by Design</h3>
            <p className="text-sm text-gray-600">Your data is encrypted and protected with industry-standard security measures.</p>
          </div>
          <div className="bg-green-50 rounded-lg p-6 text-center">
            <Eye className="w-8 h-8 text-green-600 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">Transparent Usage</h3>
            <p className="text-sm text-gray-600">We clearly explain how your information is collected and used.</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-6 text-center">
            <Users className="w-8 h-8 text-purple-600 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 mb-2">Your Control</h3>
            <p className="text-sm text-gray-600">You have control over your data and can request access, updates, or deletion.</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <FileText className="w-6 h-6 mr-2 text-blue-600" />
              Information We Collect
            </h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-3">Personal Information</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Contact information (name, email, phone number)</li>
                <li>Practice information (veterinary clinic details, staff information)</li>
                <li>Account credentials and preferences</li>
                <li>Communication preferences and settings</li>
              </ul>

              <h3 className="text-lg font-semibold mb-3 mt-6">Pet and Medical Information</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Pet owner contact information and preferences</li>
                <li>Pet details (name, breed, age, medical history as provided)</li>
                <li>Appointment scheduling information</li>
                <li>Call transcripts and AI-generated summaries</li>
                <li>Audio recordings of phone conversations (with consent)</li>
              </ul>

              <h3 className="text-lg font-semibold mb-3 mt-6">Technical Information</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Device information and browser type</li>
                <li>IP address and location data</li>
                <li>Usage analytics and performance metrics</li>
                <li>Cookies and similar tracking technologies</li>
              </ul>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <Globe className="w-6 h-6 mr-2 text-blue-600" />
              How We Use Your Information
            </h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-3">Service Delivery</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Provide AI-powered phone answering and appointment scheduling</li>
                <li>Generate call transcripts and summaries</li>
                <li>Facilitate communication between pet owners and veterinary practices</li>
                <li>Maintain accurate records and appointment histories</li>
              </ul>

              <h3 className="text-lg font-semibold mb-3 mt-6">Platform Improvement</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Improve AI model accuracy and performance</li>
                <li>Develop new features and capabilities</li>
                <li>Monitor system performance and reliability</li>
                <li>Conduct analytics to enhance user experience</li>
              </ul>

              <h3 className="text-lg font-semibold mb-3 mt-6">Communication</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Send service updates and important notifications</li>
                <li>Provide customer support and technical assistance</li>
                <li>Share relevant product updates (with your consent)</li>
                <li>Respond to inquiries and feedback</li>
              </ul>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <Lock className="w-6 h-6 mr-2 text-blue-600" />
              Data Protection & Security
            </h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-3">Security Measures</h3>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>End-to-end encryption for all sensitive data</li>
                <li>Secure cloud infrastructure with regular security audits</li>
                <li>Access controls and authentication protocols</li>
                <li>Regular security training for all team members</li>
                <li>Compliance with healthcare data protection standards</li>
              </ul>

              <h3 className="text-lg font-semibold mb-3 mt-6">Data Retention</h3>
              <p className="text-gray-700 mb-4">
                We retain your information only as long as necessary to provide our services and comply with legal obligations:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Account information: Retained while your account is active</li>
                <li>Call recordings and transcripts: Retained according to your practice's retention policy</li>
                <li>Analytics data: Aggregated and anonymized after 24 months</li>
                <li>Support communications: Retained for 3 years</li>
              </ul>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <Users className="w-6 h-6 mr-2 text-blue-600" />
              Information Sharing
            </h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700 mb-4">
                HelpPetAI does not sell, rent, or trade your personal information. We only share information in the following limited circumstances:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li><strong>With your veterinary practice:</strong> Information necessary to facilitate appointments and communication</li>
                <li><strong>Service providers:</strong> Trusted partners who help us operate our platform (under strict confidentiality agreements)</li>
                <li><strong>Legal compliance:</strong> When required by law or to protect our rights and safety</li>
                <li><strong>Business transfers:</strong> In the event of a merger or acquisition (with advance notice)</li>
              </ul>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <Eye className="w-6 h-6 mr-2 text-blue-600" />
              Your Rights & Choices
            </h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700 mb-4">You have the following rights regarding your personal information:</p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li><strong>Access:</strong> Request a copy of the personal information we have about you</li>
                <li><strong>Correction:</strong> Request corrections to inaccurate or incomplete information</li>
                <li><strong>Deletion:</strong> Request deletion of your personal information (subject to legal requirements)</li>
                <li><strong>Portability:</strong> Request your data in a portable format</li>
                <li><strong>Opt-out:</strong> Unsubscribe from marketing communications at any time</li>
                <li><strong>Consent withdrawal:</strong> Withdraw consent for specific data processing activities</li>
              </ul>
              
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>To exercise these rights:</strong> Contact us at privacy@helppet.ai or use the settings in your account dashboard.
                </p>
              </div>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Cookies & Tracking</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700 mb-4">
                We use cookies and similar technologies to improve your experience and analyze usage patterns:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li><strong>Essential cookies:</strong> Required for basic website functionality</li>
                <li><strong>Analytics cookies:</strong> Help us understand how you use our platform</li>
                <li><strong>Preference cookies:</strong> Remember your settings and preferences</li>
              </ul>
              <p className="text-gray-700 mt-4">
                You can manage cookie preferences through your browser settings or our cookie preference center.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Third-Party Services</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700 mb-4">
                Our platform integrates with third-party services to provide comprehensive functionality:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Cloud hosting and storage providers (AWS, Google Cloud)</li>
                <li>Analytics and monitoring services</li>
                <li>Communication and notification services</li>
                <li>Payment processing (if applicable)</li>
              </ul>
              <p className="text-gray-700 mt-4">
                These partners are contractually required to protect your information and use it only for the services they provide to us.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">International Data Transfers</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700">
                HelpPetAI operates primarily in the United States. If you are accessing our services from outside the U.S., 
                please be aware that your information may be transferred to, stored, and processed in the United States. 
                We ensure appropriate safeguards are in place for international data transfers in accordance with applicable privacy laws.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Children's Privacy</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700">
                HelpPetAI is designed for use by veterinary professionals and pet owners who are 18 years or older. 
                We do not knowingly collect personal information from children under 13. If we become aware that we have 
                collected personal information from a child under 13, we will take steps to delete such information promptly.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Changes to This Policy</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <p className="text-gray-700">
                We may update this privacy policy from time to time to reflect changes in our practices or applicable laws. 
                When we make material changes, we will notify you by email or through our platform. The updated policy will 
                be effective immediately upon posting, unless otherwise specified.
              </p>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Contact Us</h2>
            <div className="bg-blue-50 rounded-lg p-6">
              <p className="text-gray-700 mb-4">
                If you have questions about this privacy policy or our privacy practices, please contact us:
              </p>
              <div className="space-y-2 text-gray-700">
                <p><strong>Email:</strong> privacy@helppet.ai</p>
                <p><strong>Support:</strong> support@helppet.ai</p>
                <p><strong>Address:</strong> HelpPetAI, Inc.<br />
                [Your Business Address]<br />
                [City, State, ZIP Code]</p>
              </div>
              
              <div className="mt-6 p-4 bg-white rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>Response Time:</strong> We aim to respond to privacy-related inquiries within 30 days.
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Footer CTA */}
        <div className="text-center mt-12 p-6 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Questions about our privacy practices?</h3>
          <p className="text-gray-600 mb-4">Our team is here to help you understand how we protect your information.</p>
          <a 
            href="mailto:privacy@helppet.ai" 
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Contact Privacy Team
          </a>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
