#!/usr/bin/env python3
"""
Debug script to test search results via dev server on port 27013
"""
import json
import requests
import time
import uuid

def debug_server_search():
    """Test search via MCP server on dev port 27013"""
    
    print("=" * 60)
    print("DEBUGGING SERVER API SEARCH (DEV PORT 27013)")
    print("=" * 60)
    
    # Test parameters
    query = ""
    start_date = "2025-06-08"
    end_date = "2025-06-08"
    
    print(f"Test parameters:")
    print(f"  query: '{query}'")
    print(f"  start_date: '{start_date}'") 
    print(f"  end_date: '{end_date}'")
    print(f"  server: http://localhost:27013")
    print()
    
    # Connect to dev server
    base_url = "http://localhost:27013"
    
    print("Step 1: Connecting to SSE endpoint...")
    try:
        # Connect to SSE endpoint
        sse_response = requests.get(f"{base_url}/sse", stream=True, headers={
            "Accept": "text/event-stream"
        }, timeout=5)
        
        if sse_response.status_code != 200:
            print(f"Error connecting to SSE endpoint: {sse_response.status_code}")
            return
            
        # Read the SSE stream to get the endpoint with session ID
        import sseclient
        client = sseclient.SSEClient(sse_response)
        
        session_id = None
        for event in client.events():
            if event.event == "endpoint":
                endpoint_url = event.data
                print(f"SSE Endpoint: {endpoint_url}")
                
                # Extract session ID from URL like "/messages/?session_id=abc123"
                import re
                match = re.search(r'session_id=([^&\s]+)', endpoint_url)
                if match:
                    session_id = match.group(1)
                    print(f"Extracted session ID: {session_id}")
                break
        
        if not session_id:
            session_id = "test123"  # fallback
            print(f"Could not extract session ID, using fallback: {session_id}")
            
    except Exception as e:
        print(f"Error connecting to SSE: {e}")
        session_id = "test123"  # fallback
        print(f"Using fallback session ID: {session_id}")
    
    print("\nStep 2: Testing search_events via MCP server...")
    
    # Test the search_events method via MCP server
    url = f"{base_url}/messages/?session_id={session_id}"
    
    payload = {
        'jsonrpc': '2.0',
        'id': str(uuid.uuid4()),
        'method': 'search_events',
        'params': {
            'query': query,
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    print(f"Request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.text and response.text.strip() != "Accepted":
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            except:
                print(f"Response text: {response.text}")
        else:
            print("Response: Accepted (async processing)")
            print("Note: For async responses, check server logs or use SSE listener")
            
    except Exception as e:
        print(f"Error making request: {e}")
    
    print("\n" + "=" * 60)
    print("Step 3: Testing with time-specific search for comparison...")
    
    # Test with time-specific search
    time_payload = {
        'jsonrpc': '2.0',
        'id': str(uuid.uuid4()),
        'method': 'search_events',
        'params': {
            'query': query,
            'start_date': '2025-06-08 09:00:00',
            'end_date': '2025-06-08 17:00:00'
        }
    }
    
    print(f"Time-specific payload: {json.dumps(time_payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=time_payload, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.text and response.text.strip() != "Accepted":
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            except:
                print(f"Response text: {response.text}")
        else:
            print("Response: Accepted (async processing)")
            
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    debug_server_search() 