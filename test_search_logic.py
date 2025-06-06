#!/usr/bin/env python3
"""
Direct test of search_events function logic to verify same-day search behavior
"""
import sys
import os

# Add the src directory to the path so we can import the server module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from calendar_sse_mcp.server import search_events
import json

def test_search_events_logic():
    """Test the search_events function directly"""
    
    print("=" * 60)
    print("TESTING SEARCH_EVENTS FUNCTION LOGIC")
    print("=" * 60)
    
    # Test 1: Same-day search with empty query
    print("\nTest 1: Same-day search with empty query")
    print("Parameters: query='', start_date='2025-06-08', end_date='2025-06-08'")
    print("Expected: Should search from 2025-06-08 00:00:00 to 2025-06-08 23:59:59")
    
    try:
        result = search_events(
            query="",
            start_date="2025-06-08",
            end_date="2025-06-08"
        )
        
        print("Function executed successfully!")
        
        # Parse the JSON result
        parsed_result = json.loads(result)
        print(f"Result: {json.dumps(parsed_result, indent=2)}")
        
        # Check if there are any errors
        if "error" in parsed_result:
            print(f"❌ Error occurred: {parsed_result['error']}")
        else:
            print(f"✅ Success! Found {parsed_result.get('count', 0)} events")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # Test 2: Same day with specific time ranges (should preserve times)
    print("\nTest 2: Same day with specific times")
    print("Parameters: query='', start_date='2025-06-08 09:00:00', end_date='2025-06-08 17:00:00'")
    print("Expected: Should search from 2025-06-08 09:00:00 to 2025-06-08 17:00:00 (preserve times)")
    
    try:
        result = search_events(
            query="",
            start_date="2025-06-08 09:00:00",
            end_date="2025-06-08 17:00:00"
        )
        
        print("Function executed successfully!")
        
        # Parse the JSON result
        parsed_result = json.loads(result)
        print(f"Result: {json.dumps(parsed_result, indent=2)}")
        
        # Check if there are any errors
        if "error" in parsed_result:
            print(f"❌ Error occurred: {parsed_result['error']}")
        else:
            print(f"✅ Success! Found {parsed_result.get('count', 0)} events")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # Test 3: Different dates (should not trigger same-day logic)
    print("\nTest 3: Different dates")
    print("Parameters: query='', start_date='2025-06-08', end_date='2025-06-09'")
    print("Expected: Should search from 2025-06-08 00:00:00 to 2025-06-09 00:00:00")
    
    try:
        result = search_events(
            query="",
            start_date="2025-06-08",
            end_date="2025-06-09"
        )
        
        print("Function executed successfully!")
        
        # Parse the JSON result
        parsed_result = json.loads(result)
        print(f"Result: {json.dumps(parsed_result, indent=2)}")
        
        # Check if there are any errors
        if "error" in parsed_result:
            print(f"❌ Error occurred: {parsed_result['error']}")
        else:
            print(f"✅ Success! Found {parsed_result.get('count', 0)} events")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search_events_logic() 