#!/usr/bin/env python3
"""
Complete test script for server API search functionality with SSE response handling
"""
import json
import requests
import sseclient
import threading
import time
import uuid
import sys

def listen_for_responses(session_id, base_url, results):
    """Listen for SSE responses and store them in results dict"""
    try:
        sse_url = f"{base_url}/sse"
        response = requests.get(sse_url, stream=True, headers={
            "Accept": "text/event-stream"
        })
        
        client = sseclient.SSEClient(response)
        
        for event in client.events():
            if event.event == "message":
                try:
                    data = json.loads(event.data)
                    request_id = data.get("id")
                    if request_id:
                        results[request_id] = data
                        print(f"[SSE] Received response for request {request_id}")
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        print(f"[SSE] Error: {e}")

def test_server_search_api():
    """Test search API via MCP server with proper SSE handling"""
    
    print("=" * 70)
    print("TESTING SERVER API SEARCH (DEV PORT 27013)")
    print("=" * 70)
    
    base_url = "http://localhost:27013"
    results = {}  # Store responses by request ID
    
    # Step 1: Get session ID
    print("Step 1: Getting session ID...")
    try:
        sse_response = requests.get(f"{base_url}/sse", stream=True, headers={
            "Accept": "text/event-stream"
        }, timeout=5)
        
        if sse_response.status_code != 200:
            print(f"Error: SSE endpoint returned {sse_response.status_code}")
            return
            
        client = sseclient.SSEClient(sse_response)
        session_id = None
        
        for event in client.events():
            if event.event == "endpoint":
                endpoint_url = event.data
                print(f"Endpoint: {endpoint_url}")
                
                import re
                match = re.search(r'session_id=([^&\s]+)', endpoint_url)
                if match:
                    session_id = match.group(1)
                    print(f"Session ID: {session_id}")
                break
                
        if not session_id:
            print("Failed to get session ID")
            return
            
    except Exception as e:
        print(f"Error getting session ID: {e}")
        return
    
    # Step 2: Start SSE listener in background
    print("\nStep 2: Starting SSE listener...")
    listener_thread = threading.Thread(
        target=listen_for_responses, 
        args=(session_id, base_url, results),
        daemon=True
    )
    listener_thread.start()
    time.sleep(1)  # Give listener time to start
    
    # Step 3: Test same-day search
    print("\nStep 3: Testing same-day search (date-only inputs)...")
    url = f"{base_url}/messages/?session_id={session_id}"
    
    request_id_1 = str(uuid.uuid4())
    payload_1 = {
        'jsonrpc': '2.0',
        'id': request_id_1,
        'method': 'search_events',
        'params': {
            'query': '',
            'start_date': '2025-06-08',
            'end_date': '2025-06-08'
        }
    }
    
    print(f"Request 1: Same-day search")
    print(f"Payload: {json.dumps(payload_1['params'], indent=2)}")
    
    try:
        response = requests.post(url, json=payload_1, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 202:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Step 4: Test time-specific search
    print("\nStep 4: Testing time-specific search...")
    
    request_id_2 = str(uuid.uuid4())
    payload_2 = {
        'jsonrpc': '2.0',
        'id': request_id_2,
        'method': 'search_events',
        'params': {
            'query': '',
            'start_date': '2025-06-08 09:00:00',
            'end_date': '2025-06-08 17:00:00'
        }
    }
    
    print(f"Request 2: Time-specific search")
    print(f"Payload: {json.dumps(payload_2['params'], indent=2)}")
    
    try:
        response = requests.post(url, json=payload_2, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 202:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Step 5: Wait for responses and analyze results
    print("\nStep 5: Waiting for responses...")
    
    max_wait = 10  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if request_id_1 in results and request_id_2 in results:
            break
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)
    
    # Analyze request 1 (same-day search)
    if request_id_1 in results:
        result_1 = results[request_id_1]
        print(f"\nRequest 1 (Same-day search): SUCCESS")
        if 'result' in result_1:
            try:
                parsed_result_1 = json.loads(result_1['result'])
                events_1 = parsed_result_1.get('events', [])
                print(f"Found {len(events_1)} events")
                if events_1:
                    print("Events:")
                    for event in events_1:
                        print(f"  - {event['start']} | {event['summary']}")
                else:
                    print("No events found")
            except:
                print(f"Raw result: {result_1['result']}")
        elif 'error' in result_1:
            print(f"Error: {result_1['error']}")
    else:
        print(f"\nRequest 1 (Same-day search): NO RESPONSE")
    
    # Analyze request 2 (time-specific search)
    if request_id_2 in results:
        result_2 = results[request_id_2]
        print(f"\nRequest 2 (Time-specific search): SUCCESS")
        if 'result' in result_2:
            try:
                parsed_result_2 = json.loads(result_2['result'])
                events_2 = parsed_result_2.get('events', [])
                print(f"Found {len(events_2)} events")
                if events_2:
                    print("Events:")
                    for event in events_2:
                        print(f"  - {event['start']} | {event['summary']}")
                else:
                    print("No events found")
            except:
                print(f"Raw result: {result_2['result']}")
        elif 'error' in result_2:
            print(f"Error: {result_2['error']}")
    else:
        print(f"\nRequest 2 (Time-specific search): NO RESPONSE")
    
    # Compare results
    if request_id_1 in results and request_id_2 in results:
        print(f"\n" + "=" * 70)
        print("COMPARISON")
        print("=" * 70)
        
        try:
            result_1_data = json.loads(results[request_id_1]['result'])
            result_2_data = json.loads(results[request_id_2]['result'])
            
            events_1 = result_1_data.get('events', [])
            events_2 = result_2_data.get('events', [])
            
            print(f"Same-day search found: {len(events_1)} events")
            print(f"Time-specific search found: {len(events_2)} events")
            
            if len(events_1) >= len(events_2):
                print("✅ Same-day search found same or more events (expected)")
                print("✅ Same-day logic appears to be working correctly")
            else:
                print("❌ Same-day search found fewer events than time-specific")
                print("❌ This suggests the same-day logic may not be working")
                
        except Exception as e:
            print(f"Error comparing results: {e}")

if __name__ == "__main__":
    test_server_search_api() 