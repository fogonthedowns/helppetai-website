import React from 'react';

const PrivacyPolicy: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12 pb-6 border-b border-gray-300">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Privacy Policy</h1>
          <p className="text-sm text-gray-600">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Main Content */}
        <div className="prose prose-lg max-w-none space-y-8">
          <section>
            <p className="text-gray-700 leading-relaxed">
              Your privacy is important to us. This Privacy Policy explains how HelpPetAI ("we," "us," or "our") collects, 
              uses, and protects your information when you use our services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Information We Collect</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">1.1 Personal Information</h3>
            <p className="text-gray-700 mb-3">We may collect the following personal information:</p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Contact information (name, email address, phone number)</li>
              <li>Practice information (veterinary clinic details, staff information)</li>
              <li>Account credentials and preferences</li>
              <li>Communication preferences and settings</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">1.2 Pet and Medical Information</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Pet owner contact information and preferences</li>
              <li>Pet details (name, breed, age, medical history as provided)</li>
              <li>Appointment scheduling information</li>
              <li>Call transcripts and AI-generated summaries</li>
              <li>Audio recordings of phone conversations (with consent)</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">1.3 Technical Information</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Device information and browser type</li>
              <li>IP address and location data</li>
              <li>Usage analytics and performance metrics</li>
              <li>Cookies and similar tracking technologies</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. How We Use Your Information</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.1 Service Delivery</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Provide AI-powered phone answering and appointment scheduling</li>
              <li>Generate call transcripts and summaries</li>
              <li>Facilitate communication between pet owners and veterinary practices</li>
              <li>Maintain accurate records and appointment histories</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.2 Platform Improvement</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Improve AI model accuracy and performance</li>
              <li>Develop new features and capabilities</li>
              <li>Monitor system performance and reliability</li>
              <li>Conduct analytics to enhance user experience</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.3 Communication</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Send service updates and important notifications</li>
              <li>Provide customer support and technical assistance</li>
              <li>Share relevant product updates (with your consent)</li>
              <li>Respond to inquiries and feedback</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Data Protection and Security</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.1 Security Measures</h3>
            <p className="text-gray-700 mb-3">We implement the following security measures to protect your information:</p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>End-to-end encryption for all sensitive data</li>
              <li>Secure cloud infrastructure with regular security audits</li>
              <li>Access controls and authentication protocols</li>
              <li>Regular security training for all team members</li>
              <li>Compliance with healthcare data protection standards</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.2 Data Retention</h3>
            <p className="text-gray-700 mb-3">
              We retain your information only as long as necessary to provide our services and comply with legal obligations:
            </p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Account information: Retained while your account is active</li>
              <li>Call recordings and transcripts: Retained according to your practice's retention policy</li>
              <li>Analytics data: Aggregated and anonymized after 24 months</li>
              <li>Support communications: Retained for 3 years</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Information Sharing</h2>
            <p className="text-gray-700 mb-3">
              HelpPetAI does not sell, rent, or trade your personal information. We only share information in the following limited circumstances:
            </p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li><strong>With your veterinary practice:</strong> Information necessary to facilitate appointments and communication</li>
              <li><strong>Service providers:</strong> Trusted partners who help us operate our platform (under strict confidentiality agreements)</li>
              <li><strong>Legal compliance:</strong> When required by law or to protect our rights and safety</li>
              <li><strong>Business transfers:</strong> In the event of a merger or acquisition (with advance notice)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Your Rights and Choices</h2>
            <p className="text-gray-700 mb-3">You have the following rights regarding your personal information:</p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li><strong>Access:</strong> Request a copy of the personal information we have about you</li>
              <li><strong>Correction:</strong> Request corrections to inaccurate or incomplete information</li>
              <li><strong>Deletion:</strong> Request deletion of your personal information (subject to legal requirements)</li>
              <li><strong>Portability:</strong> Request your data in a portable format</li>
              <li><strong>Opt-out:</strong> Unsubscribe from marketing communications at any time</li>
              <li><strong>Consent withdrawal:</strong> Withdraw consent for specific data processing activities</li>
            </ul>
            <p className="text-gray-700 mt-4">
              To exercise these rights, contact us at privacy@helppet.ai or use the settings in your account dashboard.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Cookies and Tracking Technologies</h2>
            <p className="text-gray-700 mb-3">
              We use cookies and similar technologies to improve your experience and analyze usage patterns:
            </p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li><strong>Essential cookies:</strong> Required for basic website functionality</li>
              <li><strong>Analytics cookies:</strong> Help us understand how you use our platform</li>
              <li><strong>Preference cookies:</strong> Remember your settings and preferences</li>
            </ul>
            <p className="text-gray-700 mt-4">
              You can manage cookie preferences through your browser settings or our cookie preference center.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Third-Party Services</h2>
            <p className="text-gray-700 mb-3">
              Our platform integrates with third-party services to provide comprehensive functionality:
            </p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Cloud hosting and storage providers (AWS, Google Cloud)</li>
              <li>Analytics and monitoring services</li>
              <li>Communication and notification services</li>
              <li>Payment processing (if applicable)</li>
            </ul>
            <p className="text-gray-700 mt-4">
              These partners are contractually required to protect your information and use it only for the services they provide to us.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. International Data Transfers</h2>
            <p className="text-gray-700">
              HelpPetAI operates primarily in the United States. If you are accessing our services from outside the U.S., 
              please be aware that your information may be transferred to, stored, and processed in the United States. 
              We ensure appropriate safeguards are in place for international data transfers in accordance with applicable privacy laws.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Children's Privacy</h2>
            <p className="text-gray-700">
              HelpPetAI is designed for use by veterinary professionals and pet owners who are 18 years or older. 
              We do not knowingly collect personal information from children under 13. If we become aware that we have 
              collected personal information from a child under 13, we will take steps to delete such information promptly.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Changes to This Policy</h2>
            <p className="text-gray-700">
              We may update this privacy policy from time to time to reflect changes in our practices or applicable laws. 
              When we make material changes, we will notify you by email or through our platform. The updated policy will 
              be effective immediately upon posting, unless otherwise specified.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Contact Information</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about this privacy policy or our privacy practices, please contact us:
            </p>
            <div className="pl-4 space-y-2 text-gray-700">
              <p><strong>Email:</strong> privacy@helppet.ai</p>
              <p><strong>Support:</strong> support@helppet.ai</p>
              <p><strong>Mailing Address:</strong><br />
              Upcactus, Inc (DBA HelpPetAI)<br />
              5900 Balcones Drive, Suite 100
              <br />
              Austin, TX 78731</p>
            </div>
            <p className="text-gray-700 mt-4">
              We aim to respond to privacy-related inquiries within 30 days.
            </p>
          </section>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-gray-300">
          <p className="text-sm text-gray-600 text-center">
            © {new Date().getFullYear()} HelpPetAI All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;