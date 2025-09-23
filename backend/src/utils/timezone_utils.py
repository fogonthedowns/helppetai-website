"""
Timezone utilities for HelpPet.ai scheduling system

Handles timezone conversions, date boundary shifts, and iOS compatibility.
Critical for handling cases where local times cross UTC date boundaries.

Example problematic cases:
- 11:00 PM PST on Sept 23 -> 6:00 AM UTC on Sept 24
- 1:00 AM EST on Jan 1 -> 6:00 AM UTC on Jan 1 (same day, but different offset)
"""

import pytz
import logging
from datetime import datetime, date, time, timedelta
from typing import Tuple, Dict, Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class TimezoneHandler:
    """Comprehensive timezone handling for veterinary scheduling"""
    
    # Common US veterinary practice timezones
    COMMON_TIMEZONES = {
        "PST": "America/Los_Angeles",
        "PDT": "America/Los_Angeles", 
        "MST": "America/Denver",
        "MDT": "America/Denver",
        "CST": "America/Chicago",
        "CDT": "America/Chicago", 
        "EST": "America/New_York",
        "EDT": "America/New_York"
    }
    
    @classmethod
    def normalize_timezone(cls, tz_string: str) -> str:
        """
        Normalize timezone string to standard IANA format
        
        Args:
            tz_string: Timezone string (e.g., "PST", "America/Los_Angeles")
            
        Returns:
            Standard IANA timezone string
        """
        if tz_string in cls.COMMON_TIMEZONES:
            return cls.COMMON_TIMEZONES[tz_string]
        return tz_string
    
    @classmethod
    def create_local_datetime(
        cls, 
        local_date: date, 
        local_time: time, 
        timezone_str: str
    ) -> datetime:
        """
        Create timezone-aware datetime from local date/time
        
        Args:
            local_date: Local date
            local_time: Local time
            timezone_str: Timezone string
            
        Returns:
            Timezone-aware datetime object
        """
        try:
            tz_normalized = cls.normalize_timezone(timezone_str)
            tz = pytz.timezone(tz_normalized)
            
            # Create naive datetime first
            naive_dt = datetime.combine(local_date, local_time)
            
            # Localize to the specific timezone
            localized_dt = tz.localize(naive_dt)
            
            return localized_dt
            
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone_str}")
        except Exception as e:
            raise ValueError(f"Error creating local datetime: {str(e)}")
    
    @classmethod
    def convert_to_utc(
        cls,
        local_date: date,
        local_time: time, 
        timezone_str: str
    ) -> datetime:
        """
        Convert local date/time to UTC datetime
        
        Args:
            local_date: Local date
            local_time: Local time  
            timezone_str: Timezone string
            
        Returns:
            UTC datetime object
        """
        local_dt = cls.create_local_datetime(local_date, local_time, timezone_str)
        return local_dt.astimezone(pytz.UTC)
    
    @classmethod
    def analyze_date_boundary_shift(
        cls,
        local_date: date,
        start_time: time,
        end_time: time,
        timezone_str: str
    ) -> Dict[str, Any]:
        """
        Analyze potential date boundary shifts when converting to UTC
        
        This is critical for iOS scheduling where:
        - User sets 11 PM PST on Sept 23
        - UTC conversion makes it 6 AM on Sept 24
        - The date has shifted!
        
        Args:
            local_date: Original local date
            start_time: Start time in local timezone
            end_time: End time in local timezone
            timezone_str: Timezone string
            
        Returns:
            Dictionary with shift analysis
        """
        try:
            # Create local datetime objects
            local_start = cls.create_local_datetime(local_date, start_time, timezone_str)
            local_end = cls.create_local_datetime(local_date, end_time, timezone_str)
            
            # Convert to UTC
            utc_start = local_start.astimezone(pytz.UTC)
            utc_end = local_end.astimezone(pytz.UTC)
            
            # Detect date shifts
            start_date_shifted = utc_start.date() != local_start.date()
            end_date_shifted = utc_end.date() != local_end.date()
            
            # Calculate shift direction and magnitude
            start_shift_days = (utc_start.date() - local_start.date()).days
            end_shift_days = (utc_end.date() - local_end.date()).days
            
            return {
                "original_date": local_date.isoformat(),
                "timezone": timezone_str,
                
                # Local times
                "local_start": local_start.isoformat(),
                "local_end": local_end.isoformat(),
                "local_start_date": local_start.date().isoformat(),
                "local_end_date": local_end.date().isoformat(),
                
                # UTC times
                "utc_start": utc_start.isoformat(),
                "utc_end": utc_end.isoformat(), 
                "utc_start_date": utc_start.date().isoformat(),
                "utc_end_date": utc_end.date().isoformat(),
                
                # Shift analysis
                "start_date_shifted": start_date_shifted,
                "end_date_shifted": end_date_shifted,
                "start_shift_days": start_shift_days,
                "end_shift_days": end_shift_days,
                
                # Warnings
                "has_date_boundary_issues": start_date_shifted or end_date_shifted,
                "spans_multiple_utc_dates": utc_start.date() != utc_end.date(),
                
                # Timezone offset info
                "timezone_offset_start": local_start.strftime('%z'),
                "timezone_offset_end": local_end.strftime('%z'),
                "is_dst_start": bool(local_start.dst()),
                "is_dst_end": bool(local_end.dst())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing date boundary shift: {e}")
            return {
                "error": str(e),
                "original_date": local_date.isoformat() if local_date else None,
                "timezone": timezone_str
            }
    
    @classmethod
    def get_safe_storage_strategy(
        cls,
        local_date: date,
        start_time: time,
        end_time: time, 
        timezone_str: str
    ) -> Dict[str, Any]:
        """
        Recommend storage strategy based on timezone analysis
        
        Args:
            local_date: Local date
            start_time: Start time
            end_time: End time
            timezone_str: Timezone string
            
        Returns:
            Dictionary with storage recommendations
        """
        analysis = cls.analyze_date_boundary_shift(
            local_date, start_time, end_time, timezone_str
        )
        
        if analysis.get("error"):
            return {
                "strategy": "error",
                "reason": analysis["error"],
                "recommendation": "Fix timezone or time values"
            }
        
        if analysis["has_date_boundary_issues"]:
            return {
                "strategy": "timezone_aware_storage",
                "reason": "Date boundary shift detected",
                "recommendation": "Store as timezone-aware datetime objects",
                "warning": f"Local date {analysis['original_date']} spans UTC dates {analysis['utc_start_date']} to {analysis['utc_end_date']}",
                "analysis": analysis
            }
        
        if analysis["spans_multiple_utc_dates"]:
            return {
                "strategy": "careful_local_storage", 
                "reason": "Spans multiple UTC dates but no boundary shift",
                "recommendation": "Store local times with timezone metadata",
                "analysis": analysis
            }
        
        return {
            "strategy": "simple_local_storage",
            "reason": "No timezone complications detected",
            "recommendation": "Safe to store as local date/time",
            "analysis": analysis
        }


def log_timezone_analysis(
    local_date: date,
    start_time: time,
    end_time: time,
    timezone_str: str,
    context: str = "scheduling"
) -> None:
    """
    Log comprehensive timezone analysis for debugging
    
    Args:
        local_date: Local date
        start_time: Start time
        end_time: End time  
        timezone_str: Timezone string
        context: Context for logging (e.g., "iOS_scheduling", "availability_creation")
    """
    logger.info(f"🌍 TIMEZONE ANALYSIS - {context.upper()}")
    
    analysis = TimezoneHandler.analyze_date_boundary_shift(
        local_date, start_time, end_time, timezone_str
    )
    
    strategy = TimezoneHandler.get_safe_storage_strategy(
        local_date, start_time, end_time, timezone_str
    )
    
    logger.info(f"📅 Local: {analysis.get('local_start')} to {analysis.get('local_end')}")
    logger.info(f"🌐 UTC: {analysis.get('utc_start')} to {analysis.get('utc_end')}")
    
    if analysis.get("has_date_boundary_issues"):
        logger.warning("⚠️  DATE BOUNDARY SHIFT DETECTED!")
        logger.warning(f"   Local date: {analysis.get('original_date')}")
        logger.warning(f"   UTC dates: {analysis.get('utc_start_date')} to {analysis.get('utc_end_date')}")
    
    logger.info(f"💡 Recommended strategy: {strategy['strategy']}")
    logger.info(f"💡 Reason: {strategy['reason']}")
    
    if strategy.get("warning"):
        logger.warning(f"⚠️  {strategy['warning']}")
