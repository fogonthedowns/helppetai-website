import React from 'react';

const TermsOfService: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12 pb-6 border-b border-gray-300">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Terms of Service</h1>
          <p className="text-sm text-gray-600">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Main Content */}
        <div className="prose prose-lg max-w-none space-y-8">
          <section>
            <p className="text-gray-700 leading-relaxed">
              These Terms of Service ("Terms") govern your access to and use of the HelpPetAI platform and services 
              ("Services"). By accessing or using our Services, you agree to be bound by these Terms. If you do not 
              agree to these Terms, do not use our Services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Acceptance of Terms</h2>
            <p className="text-gray-700 mb-3">
              By creating an account, accessing, or using HelpPetAI services, you acknowledge that you have read, 
              understood, and agree to be bound by these Terms and our Privacy Policy. These Terms constitute a 
              legally binding agreement between you and Upcactus, Inc (DBA HelpPetAI).
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Eligibility</h2>
            <p className="text-gray-700 mb-3">
              You must meet the following requirements to use our Services:
            </p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>You are at least 18 years of age</li>
              <li>You are a licensed veterinary professional or authorized practice staff member</li>
              <li>You have the authority to bind your veterinary practice to these Terms</li>
              <li>You are not prohibited from using the Services under applicable law</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Services Description</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.1 AI-Powered Phone Services</h3>
            <p className="text-gray-700 mb-3">
              HelpPetAI provides AI-powered phone answering, appointment scheduling, call transcription, and related 
              services for veterinary practices. Our Services are designed to assist veterinary practices in managing 
              communications with pet owners.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">3.2 Service Availability</h3>
            <p className="text-gray-700 mb-3">
              We strive to provide reliable Services, but we do not guarantee uninterrupted access. Services may be 
              temporarily unavailable due to maintenance, updates, or circumstances beyond our control.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Account Registration and Security</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">4.1 Account Creation</h3>
            <p className="text-gray-700 mb-3">
              To use our Services, you must create an account and provide accurate, complete information. You are 
              responsible for maintaining the confidentiality of your account credentials.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">4.2 Account Responsibilities</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of any unauthorized access</li>
              <li>Accept responsibility for all activities under your account</li>
              <li>Ensure all account information remains accurate and current</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Acceptable Use</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.1 Permitted Use</h3>
            <p className="text-gray-700 mb-3">
              You may use our Services solely for lawful business purposes related to veterinary practice management 
              and communication with pet owners.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.2 Prohibited Activities</h3>
            <p className="text-gray-700 mb-3">You agree not to:</p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe upon intellectual property rights</li>
              <li>Transmit malicious code, viruses, or harmful content</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Use Services for spam, harassment, or fraudulent purposes</li>
              <li>Reverse engineer or attempt to extract source code</li>
              <li>Resell or redistribute our Services without authorization</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Fees and Payment</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.1 Subscription Fees</h3>
            <p className="text-gray-700 mb-3">
              Certain Services require payment of subscription fees. All fees are stated in U.S. dollars and are 
              non-refundable except as required by law or expressly stated in these Terms.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.2 Payment Terms</h3>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Fees are billed in advance on a recurring basis</li>
              <li>You authorize us to charge your payment method automatically</li>
              <li>You are responsible for all applicable taxes</li>
              <li>Failed payments may result in service suspension</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.3 Price Changes</h3>
            <p className="text-gray-700 mb-3">
              We reserve the right to modify pricing with 30 days' notice. Continued use of Services after price 
              changes constitutes acceptance of new pricing.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Intellectual Property</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">7.1 Our Rights</h3>
            <p className="text-gray-700 mb-3">
              HelpPetAI and its licensors retain all rights, title, and interest in the Services, including all 
              intellectual property rights. You are granted a limited, non-exclusive, non-transferable license to 
              use the Services in accordance with these Terms.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">7.2 Your Content</h3>
            <p className="text-gray-700 mb-3">
              You retain ownership of content you submit to our Services. By using our Services, you grant us a 
              worldwide, royalty-free license to use, store, and process your content solely to provide Services 
              to you.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Data and Privacy</h2>
            <p className="text-gray-700 mb-3">
              Our collection, use, and protection of your data is governed by our Privacy Policy. By using our 
              Services, you consent to our data practices as described in the Privacy Policy.
            </p>
            <p className="text-gray-700 mb-3">
              You are responsible for complying with all applicable privacy and data protection laws, including 
              obtaining necessary consents for call recording and data processing.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Disclaimers and Limitations</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">9.1 Service Disclaimer</h3>
            <p className="text-gray-700 mb-3 uppercase font-semibold">
              THE SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS 
              OR IMPLIED. WE DISCLAIM ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO MERCHANTABILITY, FITNESS FOR A 
              PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">9.2 Medical Disclaimer</h3>
            <p className="text-gray-700 mb-3">
              HelpPetAI Services are administrative tools only and do not provide medical advice. Veterinary 
              professionals are solely responsible for all medical decisions and diagnoses.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">9.3 Limitation of Liability</h3>
            <p className="text-gray-700 mb-3 uppercase font-semibold">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, HELPPETAI SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, 
              SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED 
              DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES.
            </p>
            <p className="text-gray-700 mb-3">
              In no event shall our total liability exceed the amount paid by you to HelpPetAI in the twelve (12) 
              months preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Indemnification</h2>
            <p className="text-gray-700 mb-3">
              You agree to indemnify, defend, and hold harmless HelpPetAI and its officers, directors, employees, 
              and agents from any claims, liabilities, damages, losses, and expenses arising from:
            </p>
            <ul className="list-disc pl-8 space-y-1 text-gray-700">
              <li>Your use of the Services</li>
              <li>Violation of these Terms</li>
              <li>Violation of any rights of another party</li>
              <li>Your content or practice's data</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Term and Termination</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">11.1 Term</h3>
            <p className="text-gray-700 mb-3">
              These Terms remain in effect while you use our Services.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">11.2 Termination by You</h3>
            <p className="text-gray-700 mb-3">
              You may terminate your account at any time through your account settings or by contacting support.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">11.3 Termination by Us</h3>
            <p className="text-gray-700 mb-3">
              We may suspend or terminate your access to Services immediately if you breach these Terms or engage 
              in prohibited activities.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">11.4 Effect of Termination</h3>
            <p className="text-gray-700 mb-3">
              Upon termination, your right to use Services ceases immediately. Provisions that by their nature 
              should survive termination shall survive, including ownership, warranty disclaimers, and limitations 
              of liability.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Modifications to Terms</h2>
            <p className="text-gray-700 mb-3">
              We reserve the right to modify these Terms at any time. We will provide notice of material changes 
              via email or through the Services. Continued use of Services after changes constitutes acceptance 
              of modified Terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Dispute Resolution</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.1 Governing Law</h3>
            <p className="text-gray-700 mb-3">
              These Terms shall be governed by the laws of the State of Texas, without regard to conflict of law 
              provisions.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.2 Arbitration</h3>
            <p className="text-gray-700 mb-3">
              Any dispute arising from these Terms or the Services shall be resolved through binding arbitration 
              in accordance with the American Arbitration Association rules, except that either party may seek 
              injunctive relief in court.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">13.3 Class Action Waiver</h3>
            <p className="text-gray-700 mb-3">
              You agree that disputes will be resolved on an individual basis and waive any right to participate 
              in a class action lawsuit or class-wide arbitration.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">14. General Provisions</h2>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">14.1 Entire Agreement</h3>
            <p className="text-gray-700 mb-3">
              These Terms, together with our Privacy Policy, constitute the entire agreement between you and 
              HelpPetAI regarding the Services.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">14.2 Severability</h3>
            <p className="text-gray-700 mb-3">
              If any provision of these Terms is found to be unenforceable, the remaining provisions will remain 
              in full force and effect.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">14.3 No Waiver</h3>
            <p className="text-gray-700 mb-3">
              Our failure to enforce any right or provision of these Terms shall not constitute a waiver of such 
              right or provision.
            </p>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">14.4 Assignment</h3>
            <p className="text-gray-700 mb-3">
              You may not assign or transfer these Terms without our prior written consent. We may assign these 
              Terms without restriction.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">15. Contact Information</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about these Terms of Service, please contact us:
            </p>
            <div className="pl-4 space-y-2 text-gray-700">
              <p><strong>Email:</strong> legal@helppet.ai</p>
              <p><strong>Support:</strong> support@helppet.ai</p>
              <p><strong>Mailing Address:</strong><br />
              Upcactus, Inc (DBA HelpPetAI)<br />
              5900 Balcones Drive, Suite 100<br />
              Austin, TX 78731</p>
            </div>
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

export default TermsOfService;
