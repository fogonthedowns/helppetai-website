//
//  PreviewSupport.swift
//  HelpPetAI
//
//  Created by Justin Zollars on 9/1/25.
//

// MARK: - Preview Support
import SwiftUI

#if DEBUG

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}

struct LoginView_Previews: PreviewProvider {
    static var previews: some View {
        LoginView()
    }
}

struct DashboardView_Previews: PreviewProvider {
    static var previews: some View {
        DashboardView(onToggleSidebar: {
            // Preview action - does nothing
        })
    }
}

struct PetDetailView_Previews: PreviewProvider {
    static var previews: some View {
        PetDetailView(petId: "sample-pet-id")
    }
}

struct AppointmentCard_Previews: PreviewProvider {
    static var previews: some View {
        AppointmentCard(appointment: .sample, status: .scheduled) {
            // Preview action
        }
        .padding()
    }
}

struct PetHeaderCard_Previews: PreviewProvider {
    static var previews: some View {
        PetHeaderCard(pet: .sample)
            .padding()
    }
}

struct MedicalRecordCard_Previews: PreviewProvider {
    static var previews: some View {
        MedicalRecordCard(record: .sample)
            .padding()
    }
}

// MARK: - Sample Data for Previews
extension Appointment {
    static let sample = Appointment(
        id: "sample-id",
        practiceId: "practice-id",
        petOwnerId: "owner-id",
        assignedVetUserId: "vet-id",
        appointmentDate: Date(),
        durationMinutes: 30,
        appointmentType: "checkup",
        status: .scheduled,
        title: "Routine Checkup - Bella",
        description: "Annual wellness exam",
        notes: nil,
        pets: [PetSummary(id: "pet-id", name: "Bella", species: "dog", breed: "Golden Retriever")],
        createdAt: Date(),
        updatedAt: Date()
    )
    
    static let inProgressSample = Appointment(
        id: "sample-id-2",
        practiceId: "practice-id",
        petOwnerId: "owner-id",
        assignedVetUserId: "vet-id",
        appointmentDate: Date(),
        durationMinutes: 45,
        appointmentType: "emergency",
        status: .inProgress,
        title: "Emergency Visit - Max",
        description: "Possible injury to left paw",
        notes: "Owner reports limping since morning",
        pets: [PetSummary(id: "pet-id-2", name: "Max", species: "dog", breed: "German Shepherd")],
        createdAt: Date(),
        updatedAt: Date()
    )
}

extension Pet {
    static let sample = Pet(
        id: "sample-pet-id",
        name: "Bella",
        species: "dog",
        breed: "Golden Retriever",
        color: "Golden",
        gender: "Female",
        weight: 65.5,
        dateOfBirth: Calendar.current.date(byAdding: .year, value: -3, to: Date()),
        microchipId: "123456789012345",
        spayedNeutered: true,
        allergies: nil,
        medications: nil,
        medicalNotes: nil,
        emergencyContact: "John Smith",
        emergencyPhone: "+1-555-123-4567",
        ownerId: "owner-id",
        isActive: true,
        createdAt: Date(),
        updatedAt: Date(),
        ageYears: 3,
        displayName: "Bella (Dog)",
        owner: PetOwner(
            id: "owner-id",
            userId: nil,
            fullName: "John Smith",
            email: "john.smith@email.com",
            phone: "+1-555-123-4567"
        )
    )
    
    static let catSample = Pet(
        id: "sample-cat-id",
        name: "Whiskers",
        species: "cat",
        breed: "Maine Coon",
        color: "Gray",
        gender: "Male",
        weight: 12.3,
        dateOfBirth: Calendar.current.date(byAdding: .year, value: -5, to: Date()),
        microchipId: "987654321098765",
        spayedNeutered: true,
        allergies: nil,
        medications: nil,
        medicalNotes: nil,
        emergencyContact: "Sarah Johnson",
        emergencyPhone: "+1-555-987-6543",
        ownerId: "owner-id-2",
        isActive: true,
        createdAt: Calendar.current.date(byAdding: .year, value: -4, to: Date())!,
        updatedAt: Date(),
        ageYears: 5,
        displayName: "Whiskers (Cat)",
        owner: PetOwner(
            id: "owner-id-2",
            userId: nil,
            fullName: "Sarah Johnson",
            email: "sarah.johnson@email.com",
            phone: "+1-555-987-6543"
        )
    )
}

extension MedicalRecord {
    static let sample = MedicalRecord(
        id: "sample-record-id",
        petId: "sample-pet-id",
        recordType: "vaccination",
        title: "Annual Vaccinations",
        description: "DHPP and Rabies vaccines administered. Pet showed no adverse reactions during or after vaccination.",
        medicalData: MedicalData(
            heartRate: "120",
            respiratoryRate: "24",
            bloodPressure: "Normal",
            bodyConditionScore: "5/9",
            dentalCondition: "Good",
            skinCondition: "Normal",
            eyeCondition: "Clear",
            earCondition: "Clean"
        ),
        visitDate: Date(),
        veterinarianName: "Dr. Sarah Johnson",
        clinicName: "Happy Paws Veterinary Clinic",
        diagnosis: nil,
        treatment: "Monitor for any delayed reactions. Follow up in 1 year for next annual vaccinations.",
        medications: "DHPP Vaccine, Rabies Vaccine",
        followUpRequired: true,
        followUpDate: Calendar.current.date(byAdding: .year, value: 1, to: Date()),
        weight: 45.2,
        temperature: 101.5,
        cost: 125.00,
        version: 1,
        isCurrent: true,
        createdByUserId: "vet-user-id",
        createdAt: Date(),
        updatedAt: Date(),
        isFollowUpDue: false,
        daysSinceVisit: 0
    )
    
    static let diagnosisSample = MedicalRecord(
        id: "sample-record-id-2",
        petId: "sample-pet-id",
        recordType: "diagnosis",
        title: "Ear Infection Treatment",
        description: "Patient presented with head shaking, ear scratching, and foul odor from left ear.",
        medicalData: MedicalData(
            heartRate: "110",
            respiratoryRate: "22",
            bloodPressure: "Normal",
            bodyConditionScore: "6/9",
            dentalCondition: "Good",
            skinCondition: "Normal",
            eyeCondition: "Clear",
            earCondition: "Infected - Left ear"
        ),
        visitDate: Calendar.current.date(byAdding: .day, value: -3, to: Date())!,
        veterinarianName: "Dr. Michael Chen",
        clinicName: "Happy Paws Veterinary Clinic",
        diagnosis: "Otitis Externa (outer ear infection) - bacterial",
        treatment: "Topical antibiotic drops twice daily for 10 days. Recheck in 2 weeks.",
        medications: "Otomax Ointment, Pain Relief Medication",
        followUpRequired: true,
        followUpDate: Calendar.current.date(byAdding: .day, value: 14, to: Date()),
        weight: 44.8,
        temperature: 102.1,
        cost: 85.50,
        version: 1,
        isCurrent: true,
        createdByUserId: "vet-user-id",
        createdAt: Calendar.current.date(byAdding: .day, value: -3, to: Date())!,
        updatedAt: Calendar.current.date(byAdding: .day, value: -3, to: Date())!,
        isFollowUpDue: true,
        daysSinceVisit: 3
    )
}

extension MedicalRecordsResponse {
    static let sample = MedicalRecordsResponse(
        records: [
            MedicalRecord.sample,
            MedicalRecord.diagnosisSample
        ],
        total: 2,
        currentRecordsCount: 2,
        historicalRecordsCount: 0
    )
}

extension DashboardResponse {
    static let sample = DashboardResponse(
        appointmentsToday: [
            Appointment.sample,
            Appointment.inProgressSample
        ],
        nextAppointment: Appointment.sample,
        currentAppointment: Appointment.inProgressSample,
        completedCount: 2,
        remainingCount: 3
    )
}

#endif
