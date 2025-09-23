"""
Unit tests for date parsing functionality in SchedulingService

Tests the _parse_date_string method with a wide variety of spoken inputs
that might come from LLM processing of phone conversations.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.phone.scheduling_service import SchedulingService


class TestDateParsing:
    """Test suite for date parsing with various spoken inputs"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a mock scheduling service (we only need the parsing method)
        self.service = SchedulingService(None)  # db_session not needed for parsing
        
        # Mock current date for consistent testing
        self.mock_now = datetime(2025, 9, 15, 10, 30)  # Monday, September 15, 2025
        self.today = self.mock_now.date()
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_relative_dates(self, mock_datetime):
        """Test relative date expressions"""
        mock_datetime.now.return_value = self.mock_now
        
        test_cases = [
            # Today/Tomorrow
            ("today", self.today),
            ("Today", self.today),
            ("TODAY", self.today),
            ("tomorrow", self.today + timedelta(days=1)),
            ("Tomorrow", self.today + timedelta(days=1)),
            ("TOMORROW", self.today + timedelta(days=1)),
            
            # Next week
            ("next week", self.today + timedelta(days=7)),
            ("Next Week", self.today + timedelta(days=7)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}'"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_weekday_names(self, mock_datetime):
        """Test weekday name parsing"""
        mock_datetime.now.return_value = self.mock_now
        
        # Current date is Monday, Sep 15, 2025
        test_cases = [
            # This week (should go to next occurrence)
            ("monday", date(2025, 9, 22)),      # Next Monday
            ("Monday", date(2025, 9, 22)),
            ("MONDAY", date(2025, 9, 22)),
            ("tuesday", date(2025, 9, 16)),     # This Tuesday
            ("Tuesday", date(2025, 9, 16)),
            ("wednesday", date(2025, 9, 17)),   # This Wednesday
            ("Wednesday", date(2025, 9, 17)),
            ("thursday", date(2025, 9, 18)),    # This Thursday
            ("friday", date(2025, 9, 19)),      # This Friday
            ("Friday", date(2025, 9, 19)),
            ("saturday", date(2025, 9, 20)),    # This Saturday
            ("sunday", date(2025, 9, 21)),      # This Sunday
            
            # Abbreviated forms
            ("mon", date(2025, 9, 22)),
            ("tue", date(2025, 9, 16)),
            ("tues", date(2025, 9, 16)),
            ("wed", date(2025, 9, 17)),
            ("thu", date(2025, 9, 18)),
            ("thur", date(2025, 9, 18)),
            ("thurs", date(2025, 9, 18)),
            ("fri", date(2025, 9, 19)),
            ("sat", date(2025, 9, 20)),
            ("sun", date(2025, 9, 21)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}' - got {result}, expected {expected}"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_next_weekday_explicit(self, mock_datetime):
        """Test explicit 'next' weekday parsing"""
        mock_datetime.now.return_value = self.mock_now
        
        # Current date is Monday, Sep 15, 2025
        test_cases = [
            # Next week explicit - should always go to following week
            ("next monday", date(2025, 9, 22)),
            ("next Tuesday", date(2025, 9, 23)),
            ("next wednesday", date(2025, 9, 24)),
            ("Next Thursday", date(2025, 9, 25)),
            ("next friday", date(2025, 9, 26)),
            ("NEXT SATURDAY", date(2025, 9, 27)),
            ("next sunday", date(2025, 9, 28)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}' - got {result}, expected {expected}"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_numeric_formats(self, mock_datetime):
        """Test numeric date formats"""
        mock_datetime.now.return_value = self.mock_now
        
        test_cases = [
            # MM-DD format (current year)
            ("9-16", date(2025, 9, 16)),
            ("09-16", date(2025, 9, 16)),
            ("12-25", date(2025, 12, 25)),
            ("1-1", date(2026, 1, 1)),  # Next year since it's past
            
            # MM/DD format
            ("9/16", date(2025, 9, 16)),
            ("09/16", date(2025, 9, 16)),
            ("12/25", date(2025, 12, 25)),
            ("1/1", date(2026, 1, 1)),  # Next year since it's past
            
            # ISO format YYYY-MM-DD
            ("2025-09-16", date(2025, 9, 16)),
            ("2025-12-25", date(2025, 12, 25)),
            ("2026-01-01", date(2026, 1, 1)),
            
            # ISO format YYYY/MM/DD
            ("2025/09/16", date(2025, 9, 16)),
            ("2025/12/25", date(2025, 12, 25)),
            ("2026/01/01", date(2026, 1, 1)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}'"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_month_names(self, mock_datetime):
        """Test month name parsing"""
        mock_datetime.now.return_value = self.mock_now
        
        test_cases = [
            # Full month names
            ("September 16", date(2025, 9, 16)),
            ("September 30", date(2025, 9, 30)),
            ("October 1", date(2025, 10, 1)),
            ("December 25", date(2025, 12, 25)),
            ("January 1", date(2026, 1, 1)),  # Next year
            ("February 14", date(2026, 2, 14)),  # Next year
            
            # Abbreviated month names
            ("Sep 16", date(2025, 9, 16)),
            ("Oct 1", date(2025, 10, 1)),
            ("Dec 25", date(2025, 12, 25)),
            ("Jan 1", date(2026, 1, 1)),  # Next year
            ("Feb 14", date(2026, 2, 14)),  # Next year
            
            # Case variations
            ("SEPTEMBER 16", date(2025, 9, 16)),
            ("september 16", date(2025, 9, 16)),
            ("September 16", date(2025, 9, 16)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}'"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_conversational_inputs(self, mock_datetime):
        """Test conversational/natural language inputs that LLMs might generate"""
        mock_datetime.now.return_value = self.mock_now
        
        test_cases = [
            # Conversational phrases
            ("I'd like an appointment on Wednesday", date(2025, 9, 17)),
            ("How about next Friday?", date(2025, 9, 26)),
            ("Can we do tomorrow?", date(2025, 9, 16)),
            ("What about today?", date(2025, 9, 15)),
            
            # With extra words
            ("on Wednesday please", date(2025, 9, 17)),
            ("maybe Friday would work", date(2025, 9, 19)),
            ("I prefer Tuesday if possible", date(2025, 9, 16)),
            ("next Monday works for me", date(2025, 9, 22)),
            
            # Date with context
            ("September 20th sounds good", date(2025, 9, 20)),
            ("How about October 5th?", date(2025, 10, 5)),
            ("Can we schedule for 12/25?", date(2025, 12, 25)),
            ("What about 9-18?", date(2025, 9, 18)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}'"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_edge_cases_and_variations(self, mock_datetime):
        """Test edge cases and variations in input"""
        mock_datetime.now.return_value = self.mock_now
        
        test_cases = [
            # Extra whitespace
            ("  wednesday  ", date(2025, 9, 17)),
            ("\ttomorrow\n", date(2025, 9, 16)),
            ("   September 20   ", date(2025, 9, 20)),
            
            # Mixed case
            ("WeDnEsDaY", date(2025, 9, 17)),
            ("ToMoRrOw", date(2025, 9, 16)),
            ("sEpTeMbEr 20", date(2025, 9, 20)),
            
            # With punctuation
            ("Wednesday.", date(2025, 9, 17)),
            ("Friday!", date(2025, 9, 19)),
            ("September 20?", date(2025, 9, 20)),
            ("9-18.", date(2025, 9, 18)),
            
            # Multiple formats in one string (should pick first valid)
            ("Wednesday or Thursday", date(2025, 9, 17)),  # Should pick Wednesday
            ("9-17 or 9-18", date(2025, 9, 17)),  # Should pick 9-17
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed for input: '{input_str}'"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_fallback_behavior(self, mock_datetime):
        """Test fallback behavior for unparseable inputs"""
        mock_datetime.now.return_value = self.mock_now
        expected_fallback = self.today + timedelta(days=1)  # Tomorrow
        
        unparseable_inputs = [
            "",  # Empty string
            "   ",  # Whitespace only
            "asdfghjkl",  # Random text
            "sometime soon",  # Vague
            "in a few days",  # Vague
            "whenever",  # Vague
            "13/45",  # Invalid date
            "February 30",  # Invalid date
            "32-15",  # Invalid date
            "xyz monday",  # Garbled
        ]
        
        for input_str in unparseable_inputs:
            result = self.service._parse_date_string(input_str)
            assert result == expected_fallback, f"Failed fallback for input: '{input_str}'"
    
    @patch('src.services.phone.scheduling_service.datetime')
    def test_year_rollover_logic(self, mock_datetime):
        """Test year rollover logic for dates in the past"""
        # Test from late in the year
        mock_datetime.now.return_value = datetime(2025, 12, 20, 10, 30)  # December 20, 2025
        
        test_cases = [
            # These should be next year since they're in the past
            ("January 1", date(2026, 1, 1)),
            ("February 14", date(2026, 2, 14)),
            ("1-1", date(2026, 1, 1)),
            ("2/14", date(2026, 2, 14)),
            
            # These should be this year since they're in the future
            ("December 25", date(2025, 12, 25)),
            ("12-25", date(2025, 12, 25)),
            ("12/31", date(2025, 12, 31)),
        ]
        
        for input_str, expected in test_cases:
            result = self.service._parse_date_string(input_str)
            assert result == expected, f"Failed year rollover for input: '{input_str}'"


# Standalone test runner for development
if __name__ == "__main__":
    """Run tests directly for development/debugging"""
    import unittest
    
    # Convert pytest-style tests to unittest format for standalone running
    suite = unittest.TestSuite()
    
    # Create test instance
    test_instance = TestDateParsing()
    test_instance.setup_method()
    
    # Add tests manually (this is a simplified version for development)
    print("🧪 Running date parsing tests...")
    print("=" * 80)
    
    try:
        # Test a few key cases
        with patch('services.phone.scheduling_service.datetime') as mock_dt:
            mock_dt.now.return_value = test_instance.mock_now
            
            # Test weekdays
            assert test_instance.service._parse_date_string("wednesday") == date(2025, 9, 17)
            assert test_instance.service._parse_date_string("next friday") == date(2025, 9, 26)
            assert test_instance.service._parse_date_string("tomorrow") == date(2025, 9, 16)
            
            print("✅ Key tests passed!")
            print("💡 Run with pytest for full test suite: python -m pytest tests/test_date_parsing.py -v")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
