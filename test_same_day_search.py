#!/usr/bin/env python3
"""
Test script to verify same-day search logic in search_events function
"""
import json
import requests
import time
from datetime import datetime

def test_same_day_search():
    """Test the same-day search functionality"""
    
    # Give the server a moment to start
    print("Waiting for server to start...")
    time.sleep(2)
    
    url = 'http://localhost:27212/messages/?session_id=test123'
    
    # Test 1: Same-day search with empty query (should capture entire day)
    payload = {
        'jsonrpc': '2.0',
        'id': 'test-same-day',
        'method': 'search_events',
        'params': {
            'query': '',
            'start_date': '2025-06-08',
            'end_date': '2025-06-08'
        }
    }
    
    print("=" * 60)
    print("TEST 1: Same-day search with empty query")
    print("=" * 60)
    print('Request:', json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f'Response status: {response.status_code}')
        if response.text and response.text.strip() != "Accepted":
            try:
                result = response.json()
                print('Response:', json.dumps(result, indent=2))
            except:
                print('Response:', response.text)
        else:
            print('Response: Accepted (async processing)')
    except Exception as e:
        print(f'Error: {e}')
    
    print("\n" + "=" * 60)
    print("TEST 2: Create test event for the same day")
    print("=" * 60)
    
    # Test 2: Create an event for the same day to verify search finds it
    create_payload = {
        'jsonrpc': '2.0',
        'id': 'create-test-event',
        'method': 'create_calendar_event',
        'params': {
            'calendar_name': 'Home',
            'summary': 'Test Same Day Search Event',
            'start_date': '2025-06-08T14:30:00',
            'end_date': '2025-06-08T15:30:00',
            'location': 'Test Location',
            'description': 'Event to test same-day search logic'
        }
    }
    
    print('Request:', json.dumps(create_payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=create_payload, timeout=10)
        print(f'Response status: {response.status_code}')
        if response.text and response.text.strip() != "Accepted":
            try:
                result = response.json()
                print('Response:', json.dumps(result, indent=2))
            except:
                print('Response:', response.text)
        else:
            print('Response: Accepted (async processing)')
    except Exception as e:
        print(f'Error: {e}')
    
    # Wait a moment for event creation
    print("\nWaiting for event creation...")
    time.sleep(3)
    
    print("\n" + "=" * 60)
    print("TEST 3: Search again after creating event")
    print("=" * 60)
    
    # Test 3: Search again to see if we find the created event
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f'Response status: {response.status_code}')
        if response.text and response.text.strip() != "Accepted":
            try:
                result = response.json()
                print('Response:', json.dumps(result, indent=2))
            except:
                print('Response:', response.text)
        else:
            print('Response: Accepted (async processing)')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_same_day_search() 