# MCP Client Connection Guide

## Correct Endpoint URLs

The Calendar HTTP MCP server uses **HTTP (Streamable HTTP)** transport. Clients should connect using standard HTTP endpoints:

### Streamable HTTP Transport Endpoints

With Streamable HTTP transport, clients use standard HTTP POST requests to the `/mcp` endpoint:

```
POST http://localhost:27212/mcp
Headers:
  Content-Type: application/json
  Accept: application/json, text/event-stream
Body:
  {
    "jsonrpc": "2.0",
    "id": "<request_id>",
    "method": "tools/list",
    "params": {}
  }
```

**Important Headers**:
- `Content-Type: application/json` - Required for request body
- `Accept: application/json, text/event-stream` - Required! Client must accept both formats

Response will be a standard HTTP response with JSON body:
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "<request_id>",
  "result": {...}
}
```

**Important**: 
- The endpoint is `/mcp` (not `/` or `/sse`)
- The `Accept` header must include both `application/json` and `text/event-stream`
- No session ID needed - direct HTTP POST requests

## Common Errors

### Error: "Network is down (os error 50)"

This error typically occurs when:
1. **Wrong endpoint**: POSTing to root `/` instead of `/mcp`
2. **Server crashed**: Check server logs at `/tmp/calendar-mcp-stderr.log`
3. **Connection dropped**: The HTTP connection was interrupted

**Solution**: 
- Ensure you're using `/mcp` endpoint for HTTP transport
- Use proper Content-Type: application/json header
- Restart the server if it crashed: `launchctl restart com.calendar-mcp`

### Error: HTTP 404

The root path `/` returns 404. Always use:
- `/mcp` for HTTP transport (standard endpoint)
- `/mcp/stream` for streaming responses (if supported)

## Testing Connection

```bash
# Test HTTP endpoint
curl -X POST http://localhost:27212/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Check server status
launchctl list | grep calendar

# View server logs
tail -f /tmp/calendar-mcp-stderr.log
```

## Client Configuration

For MCP clients using HTTP transport:

```json
{
  "mcpServers": {
    "calendar": {
      "url": "http://localhost:27212",
      "transport": "http"
    }
  }
}
```

**Important**: The client library should handle:
1. Connecting to `/sse` to get session ID
2. POSTing to `/messages/?session_id=...` for requests
3. Listening to SSE stream for responses

If your client is POSTing directly to the root URL (`http://localhost:27212/`), it's using the wrong endpoint format.
