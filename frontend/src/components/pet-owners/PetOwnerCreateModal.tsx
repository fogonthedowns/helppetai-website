import React from 'react';
import PetOwnerCreateForm from './PetOwnerCreateForm';

interface PetOwnerCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const PetOwnerCreateModal: React.FC<PetOwnerCreateModalProps> = ({ isOpen, onClose, onSuccess }) => {
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
        <PetOwnerCreateForm onClose={onClose} onSuccess={onSuccess} />
      </div>
    </div>
  );
};

export default PetOwnerCreateModal;

