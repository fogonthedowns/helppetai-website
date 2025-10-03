import React from 'react';
import PetEditForm from './PetEditForm';

interface PetEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  petId: string;
}

const PetEditModal: React.FC<PetEditModalProps> = ({ isOpen, onClose, onSuccess, petId }) => {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 bg-black bg-opacity-30 transition-opacity"
      onClick={onClose}
    >
      <div
        className="fixed right-0 top-0 h-full w-full max-w-xl bg-white shadow-2xl transform transition-transform duration-300 ease-out overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        style={{ transform: isOpen ? 'translateX(0)' : 'translateX(100%)' }}
      >
        <PetEditForm 
          onClose={onClose} 
          onSuccess={onSuccess} 
          petId={petId}
        />
      </div>
    </div>
  );
};

export default PetEditModal;

