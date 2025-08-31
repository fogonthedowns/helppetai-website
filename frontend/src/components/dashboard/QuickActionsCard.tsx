import React from 'react';
import { Link } from 'react-router-dom';
import { Plus, Calendar, FileText, Search, Stethoscope, ClipboardList } from 'lucide-react';

export const QuickActionsCard: React.FC = () => {
  const quickActions = [
    {
      icon: <Plus className="w-5 h-5" />,
      title: 'New Appointment',
      description: 'Schedule a new appointment',
      href: '/appointments/new',
      color: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      icon: <Stethoscope className="w-5 h-5" />,
      title: 'Start Visit',
      description: 'Begin visit recording',
      href: '/visit-transcripts/record',
      color: 'bg-purple-600 hover:bg-purple-700'
    }
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Card Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center">
          <Plus className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900">Quick Actions</h2>
        </div>
      </div>

      {/* Actions Grid */}
      <div className="p-6">
        <div className="grid grid-cols-1 gap-3">
          {quickActions.map((action, index) => (
            <Link
              key={index}
              to={action.href}
              className={`${action.color} text-white p-4 rounded-lg transition-all duration-200 hover:shadow-md transform hover:scale-105`}
            >
              <div className="flex items-center">
                <div className="mr-3">
                  {action.icon}
                </div>
                <div>
                  <h3 className="font-medium text-white">{action.title}</h3>
                  <p className="text-sm text-white/80">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
