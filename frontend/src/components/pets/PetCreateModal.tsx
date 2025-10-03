import React from 'react';
import PetCreateForm from './PetCreateForm';

interface PetCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  ownerUuid: string;
}

const PetCreateModal: React.FC<PetCreateModalProps> = ({ isOpen, onClose, onSuccess, ownerUuid }) => {
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
        <PetCreateForm 
          onClose={onClose} 
          onSuccess={onSuccess} 
          ownerUuid={ownerUuid}
        />
      </div>
    </div>
  );
};

export default PetCreateModal;

