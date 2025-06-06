#!/usr/bin/env python3
"""
Improved test script for the Calendar MCP Server that listens for SSE responses
"""
import json
import requests
import sseclient
import sys
import uuid
import re
import threading
import time
import argparse
from pprint import pprint

# Configuration - will be overridden by command-line arguments
DEFAULT_PORT = 27212
DEV_PORT = 27213

def get_base_url(port):
    """Get the base URL for the server"""
    return f"http://localhost:{port}"

def listen_for_sse_events(listener_session_id, base_url):
    """Listen for SSE events continuously and print responses"""
    print(f"Starting SSE listener for session {listener_session_id}...")
    
    sse_url = f"{base_url}/sse"
    response = requests.get(sse_url, stream=True, headers={
        "Accept": "text/event-stream"
    })
    
    if response.status_code != 200:
        print(f"Error connecting to SSE endpoint: {response.status_code}")
        return
    
    client = sseclient.SSEClient(response)
    
    for event in client.events():
        if event.event == "endpoint":
            print(f"Listener received endpoint: {event.data}")
        elif event.event == "message":
            try:
                data = json.loads(event.data)
                print("\n=== Received SSE Message ===")
                pprint(data)
                print("===========================\n")
            except json.JSONDecodeError:
                print(f"Non-JSON message: {event.data}")
        else:
            print(f"Event {event.event}: {event.data}")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test the Calendar MCP Server")
    parser.add_argument("--dev", action="store_true", help="Test against development server on port 27213")
    args = parser.parse_args()
    
    # Set the server port
    port = DEV_PORT if args.dev else DEFAULT_PORT
    base_url = get_base_url(port)
    
    print(f"Connecting to Calendar MCP Server at {base_url}...")
    
    # Step 1: Connect to the SSE endpoint
    response = requests.get(f"{base_url}/sse", stream=True, headers={
        "Accept": "text/event-stream"
    })
    
    if response.status_code != 200:
        print(f"Error connecting to SSE endpoint: {response.status_code}")
        return
    
    # Create SSE client
    client = sseclient.SSEClient(response)
    
    # Step 2: Get the messages endpoint from the first event
    session_id = None
    for event in client.events():
        if event.event == "endpoint":
            messages_endpoint = event.data
            print(f"Main thread received messages endpoint: {messages_endpoint}")
            
            # Extract session_id from the endpoint URL
            match = re.search(r'session_id=([^&]+)', messages_endpoint)
            if match:
                session_id = match.group(1)
                print(f"Extracted session ID: {session_id}")
            break
    
    if not session_id:
        print("Failed to extract session ID from endpoint URL")
        return
    
    # Start a background thread to listen for SSE events on a new connection
    sse_thread = threading.Thread(target=listen_for_sse_events, args=(session_id, base_url))
    sse_thread.daemon = True
    sse_thread.start()
    
    # Wait briefly to ensure the SSE listener is ready
    time.sleep(1)
    
    try:
        # Step 3: Test list_tools
        send_request(session_id, "list_tools", {}, base_url)
        time.sleep(1)  # Wait for response
        
        # Step 4: Test list_all_calendars
        send_request(session_id, "list_all_calendars", {}, base_url)
        time.sleep(2)  # Wait for response
        
        # Default calendar name
        calendar_name = "Home"
        
        # Step 5: Test creating an event
        print(f"\nCreating event in calendar: {calendar_name}")
        send_request(session_id, "create_calendar_event", {
            "calendar_name": calendar_name,
            "summary": f"Test event from MCP client at {time.strftime('%H:%M:%S')}",
            "start_date": "2023-05-10T14:00:00",
            "end_date": "2023-05-10T15:00:00",
            "location": "Test location",
            "description": "This is a test event created through the MCP server"
        }, base_url)
        
        # Wait for responses
        print("\nWaiting for responses...")
        time.sleep(3) # Reduced wait time as event creation is usually fast
        
        # Step 6: Test searching for events (default date range - likely won't find the 2023 event)
        print("\nStep 6: Searching for 'Test event from MCP client' in default date range (likely no results for old event)")
        send_request(session_id, "search_events", {
            "query": "Test event from MCP client",
            "calendar_name": calendar_name 
            # No date params: uses default 3-day window around today
        }, base_url)
        time.sleep(3) # Wait for response

        # Step 7: Test searching for the specific event created using start_date and end_date
        print("\nStep 7: Searching for the specific event created on 2023-05-10")
        send_request(session_id, "search_events", {
            "query": "Test event from MCP client",
            "calendar_name": calendar_name,
            "start_date": "2023-05-10",
            "end_date": "2023-05-10"
        }, base_url)
        time.sleep(3) # Wait for response

        # Step 8: Test searching with start_date and duration
        print("\nStep 8: Searching for events on 2023-05-10 with 1-day duration")
        send_request(session_id, "search_events", {
            "query": "Test event", # Broader query to catch the event
            "calendar_name": calendar_name,
            "start_date": "2023-05-10",
            "duration": "1d"
        }, base_url)
        time.sleep(3) # Wait for response

        # Step 9: Test searching with just duration (e.g., events in the next 7 days from today)
        # This test is more about checking if the call works; finding specific events depends on current calendar content.
        # For a predictable result, one might create an event for 'today' before this step.
        print("\nStep 9: Searching for any events in the Home calendar within the next 7 days from today")
        send_request(session_id, "search_events", {
            "query": "", # Empty query to get all events in range
            "calendar_name": calendar_name,
            "duration": "7d" # Will be today + 7 days
        }, base_url)
        time.sleep(3) # Wait for response

        # Step 10: Test same-day search with empty query 
        # This verifies the core logic: when start_date == end_date and both are date-only,
        # the search should span from 00:00:00 to 23:59:59 of that day
        print("\nStep 10: Testing same-day search - all events on 2025-06-08")
        print("Expected behavior: start_date='2025-06-08' + end_date='2025-06-08' should search 00:00:00 to 23:59:59")
        send_request(session_id, "search_events", {
            "query": "",
            "start_date": "2025-06-08",
            "end_date": "2025-06-08"
        }, base_url)
        time.sleep(3) # Wait for response

        # Create a test event for 2025-06-08 to ensure we have something to find
        print("\nStep 10a: Creating test event for 2025-06-08 to verify same-day search")
        send_request(session_id, "create_calendar_event", {
            "calendar_name": calendar_name,
            "summary": "Test event for same-day search",
            "start_date": "2025-06-08T10:00:00",
            "end_date": "2025-06-08T11:00:00",
            "location": "Test Location",
            "description": "Event created to test same-day search functionality"
        }, base_url)
        time.sleep(2) # Wait for creation

        # Now test the same-day search again to see the created event
        print("\nStep 10b: Re-testing same-day search after creating test event")
        send_request(session_id, "search_events", {
            "query": "",
            "start_date": "2025-06-08",
            "end_date": "2025-06-08"
        }, base_url)
        
        # Wait for final responses
        print("\nWaiting for final responses from new search tests...")
        time.sleep(5)
        
        print("Tests completed! Press Ctrl+C to exit.")
        
        # Keep the script running to continue receiving events
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Test interrupted by user")
    
def send_request(session_id, method, params, base_url):
    """Send a request to the MCP server and print the response"""
    request_id = str(uuid.uuid4())
    url = f"{base_url}/messages/?session_id={session_id}"
    
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    
    print(f"\n--- Sending {method} request ---")
    print(f"Request ID: {request_id}")
    
    response = requests.post(url, json=payload)
    
    print(f"Response status: {response.status_code}")
    if response.text and response.text.strip() != "Accepted":
        try:
            print("Response body:")
            pprint(response.json())
        except:
            print(f"Raw response: {response.text}")
    
    return response

if __name__ == "__main__":
    main() 