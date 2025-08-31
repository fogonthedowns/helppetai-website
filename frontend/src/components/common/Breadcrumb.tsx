import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  isActive?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items, className = '' }) => {
  return (
    <nav className={`flex items-center space-x-1 text-sm text-gray-500 ${className}`} aria-label="Breadcrumb">
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
          
          {item.href && !item.isActive ? (
            <Link
              to={item.href}
              className="hover:text-gray-700 transition-colors duration-200"
            >
              {item.label}
            </Link>
          ) : (
            <span className={item.isActive ? 'text-gray-900 font-medium' : 'text-gray-500'}>
              {item.label}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default Breadcrumb;
