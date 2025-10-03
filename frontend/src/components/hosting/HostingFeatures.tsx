import React from 'react';
import { 
  Zap, 
  Shield, 
  Globe, 
  Smartphone, 
  Clock, 
  Users, 
  TrendingUp, 
  Search,
  Lock,
  BarChart3,
  Mail,
  Calendar,
  MapPin,
  Star,
  Headphones,
  Database
} from 'lucide-react';

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
  category: 'performance' | 'security' | 'features' | 'support';
}

const features: Feature[] = [
  // Performance Features
  {
    icon: <Zap className="w-6 h-6" />,
    title: 'Lightning Fast',
    description: 'Global CDN ensures your site loads in under 2 seconds worldwide',
    category: 'performance'
  },
  {
    icon: <Globe className="w-6 h-6" />,
    title: '99.9% Uptime',
    description: 'Enterprise-grade infrastructure with guaranteed uptime SLA',
    category: 'performance'
  },
  {
    icon: <Smartphone className="w-6 h-6" />,
    title: 'Mobile Optimized',
    description: 'Perfect responsive design for all devices and screen sizes',
    category: 'performance'
  },
  {
    icon: <Database className="w-6 h-6" />,
    title: 'Auto Scaling',
    description: 'Handles traffic spikes automatically without slowdowns',
    category: 'performance'
  },

  // Security Features
  {
    icon: <Shield className="w-6 h-6" />,
    title: 'SSL Security',
    description: 'Free SSL certificates with automatic renewal and HTTPS encryption',
    category: 'security'
  },
  {
    icon: <Lock className="w-6 h-6" />,
    title: 'Daily Backups',
    description: 'Automated daily backups with one-click restore functionality',
    category: 'security'
  },
  {
    icon: <Search className="w-6 h-6" />,
    title: 'Malware Scanning',
    description: 'Continuous security monitoring and malware detection',
    category: 'security'
  },

  // Feature Set
  {
    icon: <Calendar className="w-6 h-6" />,
    title: 'Online Booking',
    description: 'Integrated appointment scheduling that syncs with your practice',
    category: 'features'
  },
  {
    icon: <TrendingUp className="w-6 h-6" />,
    title: 'SEO Optimized',
    description: 'Built-in SEO tools to rank higher in local search results',
    category: 'features'
  },
  {
    icon: <Users className="w-6 h-6" />,
    title: 'Team Profiles',
    description: 'Showcase your veterinary team with professional profiles',
    category: 'features'
  },
  {
    icon: <Mail className="w-6 h-6" />,
    title: 'Contact Forms',
    description: 'Professional contact forms with spam protection',
    category: 'features'
  },
  {
    icon: <MapPin className="w-6 h-6" />,
    title: 'Location Maps',
    description: 'Interactive Google Maps integration for easy directions',
    category: 'features'
  },
  {
    icon: <Star className="w-6 h-6" />,
    title: 'Review Integration',
    description: 'Display Google reviews and testimonials automatically',
    category: 'features'
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: 'Analytics',
    description: 'Built-in analytics to track visitors and performance',
    category: 'features'
  },

  // Support Features
  {
    icon: <Headphones className="w-6 h-6" />,
    title: '24/7 Support',
    description: 'Round-the-clock technical support from hosting experts',
    category: 'support'
  },
  {
    icon: <Clock className="w-6 h-6" />,
    title: 'Zero Maintenance',
    description: 'We handle all updates, patches, and maintenance automatically',
    category: 'support'
  }
];

interface HostingFeaturesProps {
  showCategories?: boolean;
  limit?: number;
}

const HostingFeatures: React.FC<HostingFeaturesProps> = ({ 
  showCategories = true, 
  limit 
}) => {
  const categoryColors = {
    performance: 'green',
    security: 'blue',
    features: 'purple',
    support: 'orange'
  };

  const categoryLabels = {
    performance: 'Performance',
    security: 'Security',
    features: 'Features',
    support: 'Support'
  };

  const displayFeatures = limit ? features.slice(0, limit) : features;

  const getIconColor = (category: Feature['category']) => {
    const colors = {
      performance: 'text-green-600',
      security: 'text-blue-600',
      features: 'text-purple-600',
      support: 'text-orange-600'
    };
    return colors[category];
  };

  const getBgColor = (category: Feature['category']) => {
    const colors = {
      performance: 'bg-green-100',
      security: 'bg-blue-100',
      features: 'bg-purple-100',
      support: 'bg-orange-100'
    };
    return colors[category];
  };

  if (showCategories) {
    return (
      <div className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Everything You Need</h2>
            <p className="text-xl text-gray-600">Built-in features designed specifically for veterinary practices</p>
          </div>
          
          {Object.entries(categoryLabels).map(([categoryKey, categoryLabel]) => {
            const categoryFeatures = features.filter(f => f.category === categoryKey as Feature['category']);
            
            return (
              <div key={categoryKey} className="mb-16 last:mb-0">
                <div className="flex items-center mb-8">
                  <div className={`w-1 h-8 ${categoryColors[categoryKey as keyof typeof categoryColors] === 'green' ? 'bg-green-600' : 
                    categoryColors[categoryKey as keyof typeof categoryColors] === 'blue' ? 'bg-blue-600' :
                    categoryColors[categoryKey as keyof typeof categoryColors] === 'purple' ? 'bg-purple-600' : 'bg-orange-600'} mr-4`}></div>
                  <h3 className="text-2xl font-bold text-gray-900">{categoryLabel}</h3>
                </div>
                
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {categoryFeatures.map((feature, index) => (
                    <div key={index} className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                      <div className={`w-12 h-12 ${getBgColor(feature.category)} rounded-lg flex items-center justify-center mb-4`}>
                        <div className={getIconColor(feature.category)}>
                          {feature.icon}
                        </div>
                      </div>
                      <h4 className="text-lg font-semibold mb-2 text-gray-900">{feature.title}</h4>
                      <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Everything You Need</h2>
          <p className="text-xl text-gray-600">Built-in features for veterinary practices</p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {displayFeatures.map((feature, index) => (
            <div key={index} className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow">
              <div className={`w-12 h-12 ${getBgColor(feature.category)} rounded-lg flex items-center justify-center mb-4`}>
                <div className={getIconColor(feature.category)}>
                  {feature.icon}
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900">{feature.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HostingFeatures;
