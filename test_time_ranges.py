#!/usr/bin/env python3
"""
Test to verify the exact time ranges used by search_events function
"""
import sys
import os
import dateparser
from datetime import datetime

# Add the src directory to the path so we can import the server module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_date_parsing_logic():
    """Test the exact date parsing logic used in search_events"""
    
    print("=" * 60)
    print("TESTING DATE PARSING LOGIC")
    print("=" * 60)
    
    # Test 1: Same date inputs (should trigger same-day logic)
    print("\nTest 1: Same date inputs (date-only)")
    start_date = "2025-06-08"
    end_date = "2025-06-08"
    
    parsed_start_dt = dateparser.parse(start_date)
    parsed_end_dt = dateparser.parse(end_date)
    
    print(f"Original inputs: start='{start_date}', end='{end_date}'")
    print(f"Parsed start: {parsed_start_dt}")
    print(f"Parsed end: {parsed_end_dt}")
    print(f"Same date? {parsed_start_dt.date() == parsed_end_dt.date()}")
    print(f"Both at midnight? start: {parsed_start_dt.hour}:{parsed_start_dt.minute}:{parsed_start_dt.second}, end: {parsed_end_dt.hour}:{parsed_end_dt.minute}:{parsed_end_dt.second}")
    
    # Apply our same-day logic
    start_dt = parsed_start_dt
    end_dt = parsed_end_dt
    
    if start_dt.date() == end_dt.date():
        if (start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0 and
            end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0):
            print("✅ Triggering same-day logic!")
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999)
    
    print(f"Final start: {start_dt}")  
    print(f"Final end: {end_dt}")
    
    print("\n" + "-" * 40)
    
    # Test 2: Same date with times (should NOT trigger same-day logic)
    print("\nTest 2: Same date with specific times")
    start_date = "2025-06-08 09:00:00"
    end_date = "2025-06-08 17:00:00"
    
    parsed_start_dt = dateparser.parse(start_date)
    parsed_end_dt = dateparser.parse(end_date)
    
    print(f"Original inputs: start='{start_date}', end='{end_date}'")
    print(f"Parsed start: {parsed_start_dt}")
    print(f"Parsed end: {parsed_end_dt}")
    print(f"Same date? {parsed_start_dt.date() == parsed_end_dt.date()}")
    print(f"Both at midnight? start: {parsed_start_dt.hour}:{parsed_start_dt.minute}:{parsed_start_dt.second}, end: {parsed_end_dt.hour}:{parsed_end_dt.minute}:{parsed_end_dt.second}")
    
    # Apply our same-day logic
    start_dt = parsed_start_dt
    end_dt = parsed_end_dt
    
    if start_dt.date() == end_dt.date():
        if (start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0 and
            end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0):
            print("✅ Triggering same-day logic!")
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999)
        else:
            print("❌ NOT triggering same-day logic (times are specified)")
    
    print(f"Final start: {start_dt}")  
    print(f"Final end: {end_dt}")
    
    print("\n" + "-" * 40)
    
    # Test 3: Different dates (should NOT trigger same-day logic)
    print("\nTest 3: Different dates")
    start_date = "2025-06-08"
    end_date = "2025-06-09"
    
    parsed_start_dt = dateparser.parse(start_date)
    parsed_end_dt = dateparser.parse(end_date)
    
    print(f"Original inputs: start='{start_date}', end='{end_date}'")
    print(f"Parsed start: {parsed_start_dt}")
    print(f"Parsed end: {parsed_end_dt}")
    print(f"Same date? {parsed_start_dt.date() == parsed_end_dt.date()}")
    
    # Apply our same-day logic
    start_dt = parsed_start_dt
    end_dt = parsed_end_dt
    
    if start_dt.date() == end_dt.date():
        if (start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0 and
            end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0):
            print("✅ Triggering same-day logic!")
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999)
        else:
            print("❌ NOT triggering same-day logic (times are specified)")
    else:
        print("❌ NOT triggering same-day logic (different dates)")
    
    print(f"Final start: {start_dt}")  
    print(f"Final end: {end_dt}")

if __name__ == "__main__":
    test_date_parsing_logic() 