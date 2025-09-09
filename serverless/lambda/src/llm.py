import json
import os
from anthropic import Anthropic
from typing import Dict, Any
import argparse
from datetime import datetime

class VeterinarySOAPExtractor:
    def __init__(self, api_key: str = None):
        """
        Initialize the veterinary SOAP note extractor with Anthropic API
        
        Args:
            api_key: Anthropic API key. If None, will look for ANTHROPIC_API_KEY environment variable
        """
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = Anthropic()  # Uses ANTHROPIC_API_KEY env var
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string (1 token ≈ 4 characters)
        
        Args:
            text: Input text to estimate tokens for
            
        Returns:
            Estimated number of tokens
        """
        return len(text) // 4  # Rough estimate: 1 token ≈ 4 characters

    def extract_transcript_text(self, file_content: str) -> str:
        """
        Extract clean transcript text from AWS transcription JSON
        
        Args:
            file_content: Raw file content (JSON string or plain text)
            
        Returns:
            Clean transcript text string
        """
        try:
            # If it looks like JSON, parse it and extract transcript
            if file_content.strip().startswith('{'):
                data = json.loads(file_content)
                transcript = data["results"]["transcripts"][0]["transcript"]
                print(f"✓ Extracted transcript from AWS JSON: {len(transcript)} characters")
                return transcript
            else:
                # It's already plain text
                print(f"✓ Using plain text file: {len(file_content)} characters")
                return file_content
        except Exception as e:
            print(f"⚠ Error parsing JSON, using as plain text: {e}")
            return file_content

    def get_extraction_prompt(self) -> str:
        """Return an enhanced veterinary extraction prompt for detailed SOAP analysis"""
        return """Extract veterinary visit information from the transcript for SOAP analysis. Return ONLY valid JSON with the following structure:

{
  "visit": {
    "chief_complaint": "",
    "subjective": {
      "history_of_present_illness": "",
      "owner_observations": "",
      "duration_of_symptoms": "",
      "previous_treatment": "",
      "behavior_changes": "",
      "appetite_changes": "",
      "elimination_changes": ""
    },
    "objective": {
      "vital_signs": {
        "temperature": "",
        "heart_rate": "",
        "respiratory_rate": "",
        "blood_pressure": "",
        "mucous_membrane": "",
        "capillary_refill_time": ""
      },
      "physical_exam": {
        "weight": "",
        "body_condition_score": "",
        "pain_score": "",
        "hydration_status": "",
        "eyes": "",
        "ears": "",
        "oral_cavity": "",
        "skin_coat": "",
        "musculoskeletal": "",
        "cardiovascular": "",
        "respiratory": "",
        "gastrointestinal": "",
        "neurological": "",
        "lymph_nodes": ""
      },
      "diagnostic_tests": "",
      "test_results": ""
    },
    "assessment": {
      "primary_diagnosis": "",
      "differential_diagnoses": "",
      "prognosis": ""
    },
    "plan": {
      "treatment": "",
      "medications": [
        {
          "name": "",
          "dosage": "",
          "frequency": "",
          "duration": "",
          "route": ""
        }
      ],
      "follow_up": "",
      "client_education": ""
    }
  },
  "notes": ""
}

Rules:
- Use "Not mentioned" for missing or unclear information.
- Extract only explicitly stated information from the transcript.
- Include all clinical measurements with units (e.g., temperature in °F, weight in lbs or kg, blood pressure in mmHg, body condition score on 1-9 scale, pain score on 0-10 scale).
- For ear-related complaints, extract detailed findings (e.g., debris, redness, odor, pain on palpation) under physical_exam.ears.
- For primary_diagnosis, include the most likely diagnosis or a summary of possible causes; list all mentioned causes in differential_diagnoses (e.g., "ear mites, yeast, bacterial infection").
- For medications, create a list of objects with name, dosage, frequency, duration, and route, including all prescribed treatments.
- If critical clinical data (e.g., vital signs, physical exam findings) is missing, note this in the 'notes' field with a suggestion to provide more details.
- Ensure JSON is valid, well-structured, and captures all relevant clinical details, including treatment and follow-up instructions.
- Do not infer or add information beyond the transcript.

Transcript: """

    def extract_soap_data(self, transcript: str, model: str = "claude-3-5-sonnet-latest") -> Dict[str, Any]:
        """
        Extract SOAP note data from veterinary transcript using Anthropic API
        
        Args:
            transcript: Clean transcript text
            model: Anthropic model to use (default: claude-3-5-sonnet-latest)
            
        Returns:
            Dictionary containing structured SOAP data with API call cost
        """
        try:
            prompt = self.get_extraction_prompt()
            
            # Estimate input tokens
            input_text = prompt + transcript
            input_tokens = self.estimate_tokens(input_text)
            print(f"Estimated input tokens: {input_tokens}")
            
            response = self.client.messages.create(
                model=model,
                max_tokens=1500,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": input_text
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            output_tokens = self.estimate_tokens(response_text)
            print(f"Estimated output tokens: {output_tokens}")
            
            # Calculate API call cost (Claude 3.5 Sonnet: $3/M input, $15/M output)
            input_cost = (input_tokens / 1_000_000) * 3
            output_cost = (output_tokens / 1_000_000) * 15
            total_cost = input_cost + output_cost
            
            # Try to parse JSON
            try:
                extracted_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Add extraction metadata
            extracted_data["extraction_metadata"] = {
                "extracted_at": datetime.now().isoformat(),
                "model_used": model,
                "transcript_length": len(transcript),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "api_call_cost_usd": round(total_cost, 6)
            }
            
            # Check for sparse clinical data and update notes
            objective = extracted_data.get("visit", {}).get("objective", {})
            vital_signs = objective.get("vital_signs", {})
            physical_exam = objective.get("physical_exam", {})
            has_clinical_data = any(
                value != "Not mentioned"
                for section in [vital_signs, physical_exam]
                for value in section.values()
            )
            if not has_clinical_data and extracted_data.get("notes") == "":
                extracted_data["notes"] = (
                    "Transcript lacks detailed clinical measurements (e.g., vital signs, physical exam findings). "
                    "Consider providing a more detailed transcript for comprehensive SOAP analysis."
                )
            
            return extracted_data
            
        except Exception as e:
            raise Exception(f"Error extracting SOAP data: {str(e)}")

    def process_transcript_file(self, input_file: str, output_file: str = None, model: str = "claude-3-5-sonnet-latest"):
        """
        Process a transcript file and save extracted SOAP data
        
        Args:
            input_file: Path to input file (AWS JSON or plain text)
            output_file: Path to output JSON file (optional)
            model: Anthropic model to use
        """
        try:
            print(f"Processing file: {input_file}")
            
            # Read file
            with open(input_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            print(f"Original file size: {len(file_content):,} characters")
            
            # Extract transcript text
            transcript = self.extract_transcript_text(file_content)
            
            print(f"Final transcript size: {len(transcript)} characters")
            print(f"Transcript preview: {transcript[:100]}...")
            
            # Safety check for transcript length
            if len(transcript) > 10000:
                print("⚠ WARNING: Transcript seems very long. This might cause token issues.")
                print("Consider checking if extraction worked properly.")
            
            # Extract SOAP data
            print("Calling Anthropic API...")
            extracted_data = self.extract_soap_data(transcript, model)
            
            # Determine output file name
            if not output_file:
                base_name = os.path.splitext(input_file)[0]
                output_file = f"{base_name}_veterinary_extraction.json"
            
            # Save extracted data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Extraction successful!")
            print(f"✓ Output saved to: {output_file}")
            
            # Show detailed summary
            visit = extracted_data.get('visit', {})
            chief_complaint = visit.get('chief_complaint', 'Not specified')
            primary_diagnosis = visit.get('assessment', {}).get('primary_diagnosis', 'Not specified')
            weight = visit.get('objective', {}).get('physical_exam', {}).get('weight', 'Not specified')
            temperature = visit.get('objective', {}).get('vital_signs', {}).get('temperature', 'Not specified')
            heart_rate = visit.get('objective', {}).get('vital_signs', {}).get('heart_rate', 'Not specified')
            respiratory_rate = visit.get('objective', {}).get('vital_signs', {}).get('respiratory_rate', 'Not specified')
            ears = visit.get('objective', {}).get('physical_exam', {}).get('ears', 'Not specified')
            oral_cavity = visit.get('objective', {}).get('physical_exam', {}).get('oral_cavity', 'Not specified')
            cardiovascular = visit.get('objective', {}).get('physical_exam', {}).get('cardiovascular', 'Not specified')
            respiratory = visit.get('objective', {}).get('physical_exam', {}).get('respiratory', 'Not specified')
            treatment = visit.get('plan', {}).get('treatment', 'Not specified')
            medications = visit.get('plan', {}).get('medications', [])
            follow_up = visit.get('plan', {}).get('follow_up', 'Not specified')
            api_call_cost = extracted_data.get('extraction_metadata', {}).get('api_call_cost_usd', 'Not calculated')
            
            print(f"\nSummary:")
            print(f"Chief Complaint: {chief_complaint}")
            print(f"Primary Diagnosis: {primary_diagnosis}")
            print(f"Weight: {weight}")
            print(f"Temperature: {temperature}")
            print(f"Heart Rate: {heart_rate}")
            print(f"Respiratory Rate: {respiratory_rate}")
            print(f"Ears: {ears}")
            print(f"Oral Cavity: {oral_cavity}")
            print(f"Cardiovascular: {cardiovascular}")
            print(f"Respiratory: {respiratory}")
            print(f"Treatment: {treatment}")
            print(f"Medications: {', '.join([f'{med['name']} ({med['dosage']}, {med['frequency']}, {med['duration']})' for med in medications]) or 'None'}")
            print(f"Follow-up: {follow_up}")
            print(f"API Call Cost: ${api_call_cost:.6f}")
            
            return extracted_data
            
        except Exception as e:
            print(f"❌ Error processing transcript: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Extract veterinary SOAP notes from transcripts using Anthropic API')
    parser.add_argument('input_file', help='Path to transcript file (AWS JSON or plain text)')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-m', '--model', default='claude-3-5-sonnet-latest', help='Anthropic model to use')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
    
    args = parser.parse_args()
    
    try:
        # Initialize extractor
        extractor = VeterinarySOAPExtractor(api_key=args.api_key)
        
        # Process transcript
        extracted_data = extractor.process_transcript_file(
            args.input_file, 
            args.output, 
            args.model
        )
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())