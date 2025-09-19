import React from 'react';
import { Link } from 'react-router-dom';
import { Stethoscope } from 'lucide-react';

const Footer = () => {
  return (
    <>
      {/* PIMS Integration CTA Section */}
      {/* <section className="bg-gradient-to-br from-purple-500 to-indigo-600 py-24 w-full">
        <div className="w-full px-6">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-5xl font-bold text-white mb-6 leading-tight">
              Connect HelpPet.ai With<br />
              Your PIMS?
            </h2>
            <p className="text-xl text-purple-100 mb-8">
              Connect HelpPet.ai with your current Practice Information Management System and see the difference. Schedule a live demo today and start transforming your documentation process.
            </p>
            <button className="bg-white text-purple-600 px-8 py-4 rounded-lg text-lg font-bold hover:bg-gray-100 transition-colors">
              Book Your Demo Now
            </button>
          </div>
        </div>
      </section> */}

      {/* Footer */}
      <footer className="bg-white py-16 border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            {/* Brand Section */}
            <div className="md:col-span-1">
              <div className="flex items-center space-x-2 mb-6">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Stethoscope className="w-4 h-4 text-white" />
                </div>
                <span className="text-2xl font-bold text-gray-900">HelpPet.ai</span>
              </div>
              <p className="text-gray-600 leading-relaxed mb-6">
                HelpPet.ai, we are committed to revolutionizing veterinary visit documentation through innovative AI-powered solutions. Our platform empowers veterinary practices to streamline workflows, improve accuracy, and save valuable time, allowing veterinarians to focus on what truly matters, your pets.
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
                  <Link to="/vets" className="text-gray-600 hover:text-blue-600 transition-colors">
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
                © 2025 HelpPet.ai. All rights reserved.
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
