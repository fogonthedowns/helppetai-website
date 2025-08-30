/**
 * Pet-related TypeScript types
 */

export interface Pet {
  id: string;
  owner_id: string;
  name: string;
  species: string;
  breed?: string;
  color?: string;
  gender?: string;
  weight?: number;
  date_of_birth?: string; // ISO date string
  microchip_id?: string;
  spayed_neutered?: boolean;
  allergies?: string;
  medications?: string;
  medical_notes?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  age_years?: number;
  display_name: string;
}

export interface PetWithOwner extends Pet {
  owner: {
    id: string;
    user_id?: string;
    full_name: string;
    email?: string;
    phone?: string;
  };
}

export interface PetFormData {
  name: string;
  species: string;
  breed?: string;
  color?: string;
  gender?: string;
  weight?: number;
  date_of_birth?: string;
  microchip_id?: string;
  spayed_neutered?: boolean;
  allergies?: string;
  medications?: string;
  medical_notes?: string;
  emergency_contact?: string;
  emergency_phone?: string;
}

export interface PetCreateRequest extends PetFormData {
  owner_id: string;
}

export interface PetUpdateRequest extends Partial<PetFormData> {
  is_active?: boolean;
}

export interface PetListResponse {
  pets: Pet[];
  total: number;
  page: number;
  per_page: number;
}

export const PET_SPECIES_OPTIONS = [
  'Dog',
  'Cat',
  'Bird',
  'Rabbit',
  'Horse',
  'Reptile',
  'Fish',
  'Other'
] as const;

export const PET_GENDER_OPTIONS = [
  'Male',
  'Female',
  'Unknown'
] as const;

export type PetSpecies = typeof PET_SPECIES_OPTIONS[number];
export type PetGender = typeof PET_GENDER_OPTIONS[number];
