/**
 * Phone number formatting utilities
 */

export const formatPhoneNumber = (value: string): string => {
  // Remove all non-numeric characters
  const phoneNumber = value.replace(/\D/g, '');
  
  // Don't format if empty
  if (!phoneNumber) return '';
  
  // Format based on length
  if (phoneNumber.length <= 3) {
    return phoneNumber;
  } else if (phoneNumber.length <= 6) {
    return `(${phoneNumber.slice(0, 3)}) ${phoneNumber.slice(3)}`;
  } else if (phoneNumber.length <= 10) {
    return `(${phoneNumber.slice(0, 3)}) ${phoneNumber.slice(3, 6)}-${phoneNumber.slice(6)}`;
  } else {
    // For numbers longer than 10 digits, format as +1 (xxx) xxx-xxxx
    return `+${phoneNumber.slice(0, 1)} (${phoneNumber.slice(1, 4)}) ${phoneNumber.slice(4, 7)}-${phoneNumber.slice(7, 11)}`;
  }
};

export const unformatPhoneNumber = (formattedPhone: string): string => {
  // Remove all non-numeric characters for storage
  return formattedPhone.replace(/\D/g, '');
};

export const isValidPhoneNumber = (phoneNumber: string): boolean => {
  // Remove formatting and check if it's a valid US phone number (10 digits)
  const digits = phoneNumber.replace(/\D/g, '');
  return digits.length === 10 || digits.length === 11; // 10 for US, 11 for +1 US
};

export const handlePhoneInput = (
  e: React.ChangeEvent<HTMLInputElement>,
  setFormData: React.Dispatch<React.SetStateAction<any>>,
  fieldName: string
) => {
  const formatted = formatPhoneNumber(e.target.value);
  setFormData((prev: any) => ({
    ...prev,
    [fieldName]: formatted
  }));
};
