import React from 'react';
import AppointmentEditForm from './AppointmentEditForm';

interface AppointmentEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  appointmentId: string;
  onSuccess?: () => void;
}

const AppointmentEditModal: React.FC<AppointmentEditModalProps> = ({
  isOpen,
  onClose,
  appointmentId,
  onSuccess
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-30 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal Panel */}
      <div className="absolute inset-y-0 right-0 flex max-w-xl w-full">
        <div className="bg-white w-full shadow-2xl">
          <AppointmentEditForm 
            appointmentId={appointmentId}
            onClose={onClose}
            onSuccess={onSuccess}
          />
        </div>
      </div>
    </div>
  );
};

export default AppointmentEditModal;

