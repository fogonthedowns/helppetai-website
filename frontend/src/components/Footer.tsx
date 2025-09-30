import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <>
      {/* Footer */}
      <footer className="bg-white py-16 border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            {/* Brand Section */}
            <div className="md:col-span-1">
              <div className="flex items-center space-x-2 mb-6">
                <img 
                  src="/logo_clear_back.png" 
                  alt="HelpPetAI Logo" 
                  width="32" 
                  height="32" 
                  className="object-contain"
                />
                <span className="text-2xl font-bold text-gray-900">HelpPetAI</span>
              </div>
              <p className="text-gray-600 leading-relaxed mb-6">
                Our AI voice agent manages routine inbound and outbound calls, from scheduling appointments to answering common questions, taking up to 80% of the load off your staff. 
              </p>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Links</h3>
              <ul className="space-y-3">
                <li>
                  <Link to="/" className="text-gray-600 hover:text-blue-600 transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <Link to="/about" className="text-gray-600 hover:text-blue-600 transition-colors">
                    About Us
                  </Link>
                </li>
                <li>
                  <Link to="/contact" className="text-gray-600 hover:text-blue-600 transition-colors">
                    Contact Us
                  </Link>
                </li>
                <li>
                  <Link to="/practices" className="text-gray-600 hover:text-blue-600 transition-colors">
                    Veterinary Practices
                  </Link>
                </li>
              </ul>
            </div>

            {/* Legal Pages */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Legal Pages</h3>
              <ul className="space-y-3">
                <li>
                  <Link to="/privacy" className="text-gray-600 hover:text-blue-600 transition-colors">
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link to="/terms" className="text-gray-600 hover:text-blue-600 transition-colors">
                    Terms of Service
                  </Link>
                </li>
                <li>
                  <Link to="/security" className="text-gray-600 hover:text-blue-600 transition-colors">
                    Security & Compliance
                  </Link>
                </li>
              </ul>
            </div>

            {/* Social Media */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Social Media</h3>
              <ul className="space-y-3">
                <li>
                  <a 
                    href="https://linkedin.com/company/helppetai" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                  >
                    LinkedIn
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Border */}
          <div className="border-t border-gray-200 mt-12 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-500 text-sm">
                © 2025 HelpPetAI. All rights reserved.
              </p>
              <p className="text-gray-500 text-sm mt-4 md:mt-0">
                  Voice-First Platform • Front Desk Simplified
              </p>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
};

export default Footer;
