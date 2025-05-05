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
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:27212"

def listen_for_sse_events(listener_session_id):
    """Listen for SSE events continuously and print responses"""
    print(f"Starting SSE listener for session {listener_session_id}...")
    
    sse_url = f"{BASE_URL}/sse"
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
    print("Connecting to Calendar MCP Server...")
    
    # Step 1: Connect to the SSE endpoint
    response = requests.get(f"{BASE_URL}/sse", stream=True, headers={
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
    sse_thread = threading.Thread(target=listen_for_sse_events, args=(session_id,))
    sse_thread.daemon = True
    sse_thread.start()
    
    # Wait briefly to ensure the SSE listener is ready
    time.sleep(1)
    
    try:
        # Step 3: Test list_tools
        send_request(session_id, "list_tools", {})
        time.sleep(1)  # Wait for response
        
        # Step 4: Test list_all_calendars
        send_request(session_id, "list_all_calendars", {})
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
        })
        
        # Wait for responses
        print("\nWaiting for responses...")
        time.sleep(5)
        
        # Step 6: Test searching for events
        send_request(session_id, "search_events", {
            "query": "Test event from MCP client",
            "calendar_name": calendar_name
        })
        
        # Wait for final responses
        print("\nWaiting for final responses...")
        time.sleep(5)
        
        print("Tests completed! Press Ctrl+C to exit.")
        
        # Keep the script running to continue receiving events
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Test interrupted by user")
    
def send_request(session_id, method, params):
    """Send a request to the MCP server and print the response"""
    request_id = str(uuid.uuid4())
    url = f"{BASE_URL}/messages/?session_id={session_id}"
    
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