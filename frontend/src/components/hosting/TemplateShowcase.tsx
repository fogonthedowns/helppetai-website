import React, { useState } from 'react';
import { Check, Monitor, Smartphone, Eye } from 'lucide-react';

interface Template {
  id: string;
  name: string;
  description: string;
  image: string;
  features: string[];
  category: 'modern' | 'classic' | 'minimal' | 'professional';
  preview: string;
  popular?: boolean;
}

const templates: Template[] = [
  {
    id: 'modern-vet',
    name: 'Modern Veterinary',
    description: 'Clean, contemporary design with appointment booking integration',
    image: 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=400&h=300&fit=crop&crop=center',
    features: ['Online Appointments', 'Service Showcase', 'Team Profiles', 'Contact Forms'],
    category: 'modern',
    preview: '#',
    popular: true
  },
  {
    id: 'classic-care',
    name: 'Classic Care',
    description: 'Traditional, trustworthy design that builds client confidence',
    image: 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=300&fit=crop&crop=center',
    features: ['Professional Layout', 'Testimonials', 'Services Grid', 'Location Map'],
    category: 'classic',
    preview: '#'
  },
  {
    id: 'minimal-practice',
    name: 'Minimal Practice',
    description: 'Simple, fast-loading design focused on essential information',
    image: 'https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=400&h=300&fit=crop&crop=center',
    features: ['Fast Loading', 'Mobile First', 'Essential Info', 'Easy Navigation'],
    category: 'minimal',
    preview: '#'
  },
  {
    id: 'premium-clinic',
    name: 'Premium Clinic',
    description: 'Luxury design for high-end veterinary practices',
    image: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=400&h=300&fit=crop&crop=center',
    features: ['Premium Design', 'Video Backgrounds', 'Advanced Animations', 'Custom Branding'],
    category: 'professional',
    preview: '#',
    popular: true
  },
  {
    id: 'family-friendly',
    name: 'Family Friendly',
    description: 'Warm, welcoming design perfect for family pet practices',
    image: 'https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400&h=300&fit=crop&crop=center',
    features: ['Friendly Design', 'Pet Gallery', 'Family Focus', 'Community Feel'],
    category: 'modern',
    preview: '#'
  },
  {
    id: 'emergency-ready',
    name: 'Emergency Ready',
    description: 'Urgent care focused with clear emergency information',
    image: 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=400&h=300&fit=crop&crop=center',
    features: ['Emergency Info', 'Quick Contact', 'Urgent Design', '24/7 Messaging'],
    category: 'professional',
    preview: '#'
  }
];

interface TemplateShowcaseProps {
  onTemplateSelect?: (template: Template) => void;
  selectedTemplate?: Template | null;
}

const TemplateShowcase: React.FC<TemplateShowcaseProps> = ({ 
  onTemplateSelect, 
  selectedTemplate 
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  const filteredTemplates = selectedCategory === 'all' 
    ? templates 
    : templates.filter(template => template.category === selectedCategory);

  const categories = [
    { key: 'all', label: 'All Templates', count: templates.length },
    { key: 'modern', label: 'Modern', count: templates.filter(t => t.category === 'modern').length },
    { key: 'classic', label: 'Classic', count: templates.filter(t => t.category === 'classic').length },
    { key: 'minimal', label: 'Minimal', count: templates.filter(t => t.category === 'minimal').length },
    { key: 'professional', label: 'Professional', count: templates.filter(t => t.category === 'professional').length }
  ];

  return (
    <div className="py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Choose Your Template</h2>
          <p className="text-xl text-gray-600 mb-8">Professional designs crafted specifically for veterinary practices</p>
          
          {/* Category Filter */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            {categories.map((category) => (
              <button
                key={category.key}
                onClick={() => setSelectedCategory(category.key)}
                className={`px-6 py-3 rounded-full font-medium transition-all duration-200 ${
                  selectedCategory === category.key 
                    ? 'bg-blue-600 text-white shadow-lg transform scale-105' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
                }`}
              >
                {category.label}
                <span className="ml-2 text-xs opacity-75">({category.count})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Template Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredTemplates.map((template) => (
            <div 
              key={template.id} 
              className={`bg-white rounded-xl shadow-lg overflow-hidden transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 ${
                selectedTemplate?.id === template.id ? 'ring-4 ring-blue-500' : ''
              }`}
              onMouseEnter={() => setHoveredTemplate(template.id)}
              onMouseLeave={() => setHoveredTemplate(null)}
            >
              {/* Template Image */}
              <div className="aspect-video bg-gray-200 relative overflow-hidden">
                <img 
                  src={template.image} 
                  alt={template.name}
                  className="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
                />
                
                {/* Popular Badge */}
                {template.popular && (
                  <div className="absolute top-4 left-4 bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
                    Popular
                  </div>
                )}
                
                {/* Category Badge */}
                <div className="absolute top-4 right-4 bg-black bg-opacity-70 text-white px-3 py-1 rounded-full text-xs font-medium capitalize">
                  {template.category}
                </div>
                
                {/* Hover Overlay */}
                <div className={`absolute inset-0 bg-black transition-opacity duration-300 flex items-center justify-center ${
                  hoveredTemplate === template.id ? 'bg-opacity-40 opacity-100' : 'bg-opacity-0 opacity-0'
                }`}>
                  <div className="flex gap-3">
                    <button className="bg-white text-gray-900 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      Preview
                    </button>
                    <button className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2">
                      <Monitor className="w-4 h-4" />
                      Select
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Template Content */}
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xl font-semibold text-gray-900">{template.name}</h3>
                  <div className="flex items-center gap-1">
                    <Monitor className="w-4 h-4 text-gray-400" />
                    <Smartphone className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
                
                <p className="text-gray-600 mb-4 text-sm leading-relaxed">{template.description}</p>
                
                {/* Features */}
                <div className="space-y-2 mb-6">
                  {template.features.slice(0, 3).map((feature, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </div>
                  ))}
                  {template.features.length > 3 && (
                    <div className="text-xs text-gray-500 ml-6">
                      +{template.features.length - 3} more features
                    </div>
                  )}
                </div>
                
                {/* Action Buttons */}
                <div className="flex gap-3">
                  <button 
                    onClick={() => onTemplateSelect?.(template)}
                    className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-all duration-200 hover:shadow-lg"
                  >
                    Choose Template
                  </button>
                  <button className="border-2 border-gray-200 text-gray-700 py-3 px-4 rounded-lg font-medium hover:border-blue-300 hover:text-blue-600 transition-all duration-200">
                    Preview
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* No Templates Message */}
        {filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Monitor className="w-16 h-16 mx-auto" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No templates found</h3>
            <p className="text-gray-600">Try selecting a different category</p>
          </div>
        )}

        {/* Template Stats */}
        <div className="mt-16 bg-gray-50 rounded-2xl p-8">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">{templates.length}</div>
              <div className="text-gray-600">Professional Templates</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 mb-2">99.9%</div>
              <div className="text-gray-600">Uptime Guarantee</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">&lt;2s</div>
              <div className="text-gray-600">Average Load Time</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateShowcase;
