"""Simple phone number utilities for caller matching."""

import re
from typing import Optional


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalize phone number to digits only for matching.
    
    Examples:
        "+1 (555) 123-4567" -> "15551234567"
        "555.123.4567" -> "5551234567"
        "(555) 123-4567" -> "5551234567"
    """
    if not phone:
        return None
    
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', phone)
    
    # Handle US numbers - remove leading 1 if present and length is 11
    if len(digits_only) == 11 and digits_only.startswith('1'):
        digits_only = digits_only[1:]
    
    # Return 10-digit number or None if invalid
    if len(digits_only) == 10:
        return digits_only
    
    return None


def phones_match(phone1: Optional[str], phone2: Optional[str]) -> bool:
    """Check if two phone numbers match after normalization."""
    norm1 = normalize_phone(phone1)
    norm2 = normalize_phone(phone2)
    
    return norm1 is not None and norm1 == norm2
