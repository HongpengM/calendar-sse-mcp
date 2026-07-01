#!/usr/bin/env python3
"""OpenCode stdio bridge for calendar-http-mcp.

Translates between OpenCode's stdio MCP transport and the server's
Streamable HTTP transport (which requires session management).
Assumes the calendar MCP server is already running on port 27212.
"""
import json
import sys
import urllib.request
import urllib.error

SERVER_URL = "http://127.0.0.1:27212/mcp"
REQ_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _send(session_id, body):
    data = json.dumps(body).encode("utf-8")
    headers = dict(REQ_HEADERS)
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(SERVER_URL, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read().decode("utf-8"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8"), dict(e.headers)


def _parse_sse(text):
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:])
    return None


def _get_session_id(headers):
    for k, v in headers.items():
        if k.lower() == "mcp-session-id":
            return v
    return None


def main():
    # Establish session with the Streamable HTTP server
    sid = None
    probe = {"jsonrpc": "2.0", "id": 0, "method": "ping", "params": {}}
    _, hdrs = _send(None, probe)
    sid = _get_session_id(hdrs) or ""

    # Initialize
    text, _ = _send(sid, {
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "opencode-bridge", "version": "1.0"},
        },
    })
    if _parse_sse(text) and "result" in _parse_sse(text):
        _send(sid, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    print("Bridge ready", file=sys.stderr, flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method", "")
        req_id = req.get("id")

        if method == "initialize":
            print(json.dumps({
                "jsonrpc": "2.0", "id": req_id, "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "experimental": {},
                        "prompts": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {"name": "Calendar MCP", "version": "1.0"},
                },
            }), flush=True)
            continue

        if method == "notifications/initialized":
            continue

        text, _ = _send(sid, req)
        parsed = _parse_sse(text)
        if parsed:
            print(json.dumps(parsed), flush=True)
        else:
            try:
                print(json.dumps(json.loads(text)), flush=True)
            except json.JSONDecodeError:
                print(json.dumps({
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32700, "message": f"Parse error: {text[:200]}"},
                }), flush=True)


if __name__ == "__main__":
    main()
