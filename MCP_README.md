# MCP Server Implementation

This project now includes a **Model Context Protocol (MCP) Server** that exposes Dhia's platform database to Haotian's RAG system via a clean, standardized interface.

## Overview

The MCP server allows Haotian's RAG agent to query platform data, user analytics, and conversation history without direct database access. All communication happens through a single HTTP endpoint using JSON-RPC 2.0.

```
┌─────────────────────────────┐
│ Haotian's RAG Agent         │
│ (MCP Client)                │
└──────────────┬──────────────┘
               │ POST /mcp
               │ (JSON-RPC 2.0)
               ▼
┌──────────────────────────────┐
│ Dhia's MCP Server            │
│ (This Project)               │
│ ├─ query_platform_supporting │
│ ├─ Database Repository       │
│ └─ Auth Service              │
└──────────────────────────────┘
```

## Quick Start

### For Dhia (Server Setup)

```bash
# Start the MCP server
python mcp_launcher.py
# Server runs on http://0.0.0.0:8000/mcp
```

Or with custom port:
```bash
MCP_PORT=9000 python mcp_launcher.py
```

### For Haotian (Client Setup)

1. Get the MCP server URL from Dhia: `http://<dhia-host>:8000/mcp`
2. Register in your agent config (YAML):
   ```yaml
   mcp_servers:
     platform_supporting:
       transport: streamable_http
       url: http://<dhia-host>:8000/mcp
   ```
3. Discover tools at startup with `tools/list` request
4. Call `query_platform_supporting` when users ask platform questions

### Test the Integration

```bash
# Automated test suite
python test_mcp.py --host=http://localhost:8000

# Interactive query mode
python test_mcp.py --interactive
```

## Architecture

### Server Side (Dhia)

| Component | File | Purpose |
|-----------|------|---------|
| MCP Server | `mcp_server.py` | HTTP handler + JSON-RPC implementation |
| Launcher | `mcp_launcher.py` | Start server with DB/Auth init |
| Agent | `mcp_server.py:PlatformSupportingAgent` | Query logic + response formatting |

### Client Side (Haotian)

- Discovers available tools via `tools/list` request
- Calls `query_platform_supporting` with natural language questions
- Parses JSON response containing the answer

## The Tool

### `query_platform_supporting`

**Input:** Natural language query string

**Output:** Formatted text answer about platform data

**Supported Questions:**

✅ User Statistics
```
"show me system statistics"
"what are total users?"
"platform overview"
```

✅ User Lookups  
```
"lookup user john@example.com"
"find user by email"
"show all users"
```

✅ Conversation History
```
"show recent conversations"
"get chat records"
"latest messages"
```

✅ Timeseries Analytics
```
"conversation trends for last 7 days"
"analytics over 14 days"
"hourly trends"
```

✅ System Health
```
"system status"
"is platform healthy?"
"health check"
```

## API Specification

### Endpoint

```
POST http://<host>:8000/mcp
Content-Type: application/json
```

### List Tools Request

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "query_platform_supporting",
        "description": "Query platform database for statistics, users, conversations...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": { "type": "string" }
          },
          "required": ["query"]
        }
      }
    ]
  }
}
```

### Query Tool Request

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "query_platform_supporting",
    "arguments": {
      "query": "show me user statistics"
    }
  },
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"📊 Platform Statistics:\n  • Total Users: 42\n  • Total Conversations: 1,250\n  • Active Users (last 7 days): 18\n  • Average Response Time: 320ms\"}"
      }
    ]
  }
}
```

## Files

### Core Implementation
- **`mcp_server.py`** - Main MCP server with HTTP handler and agent logic (381 lines)
- **`mcp_launcher.py`** - Production launcher script (62 lines)

### Testing & Documentation  
- **`test_mcp.py`** - Comprehensive test suite + interactive client (239 lines)
- **`docs_md/MCP_SERVER_GUIDE.md`** - Complete API documentation (474 lines)
- **`MCP_INTEGRATION_SUMMARY.md`** - Quick integration guide for Haotian (236 lines)
- **`MCP_README.md`** - This file

## Example Usage

### Using curl

```bash
# Test connection
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'

# Query statistics
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "show me user statistics"
      }
    },
    "id": 1
  }'
```

### Using Python Client

```python
from test_mcp import MCPTestClient

client = MCPTestClient("http://localhost:8000")

# Discover tools
tools = client.list_tools()

# Query
result = client.query("show me system statistics")
```

### Using JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'query_platform_supporting',
      arguments: {
        query: 'show me user statistics'
      }
    },
    id: 1
  })
});

const data = await response.json();
const answer = JSON.parse(data.result.content[0].text).answer;
console.log(answer);
```

## Configuration

### Environment Variables

- `MCP_PORT` - Port for MCP server (default: 8000)
- `OPENAI_API_KEY` - (Required by main app)
- Other config from `config.py`

### Integration with Haotian

Add to your agent's system prompt:

```
When the user asks about platform metrics, user data, conversation history, 
or system analytics, use the query_platform_supporting tool from the 
platform_supporting MCP server. For all other queries, use your primary 
data catalog.
```

## Performance

- **Response Time:** < 2 seconds typical, < 60 seconds guaranteed
- **Database:** SQLite with proper indexing
- **Queries:** Optimized for common analytics questions
- **Concurrency:** HTTP server handles multiple simultaneous requests

## Security

⚠️ **Notes:**
- No authentication (assume internal network)
- Database contains user conversation history
- For production external exposure: Add API key authentication
- See `docs_md/MCP_SERVER_GUIDE.md` for details

## Troubleshooting

### Server won't start
```bash
# Check port usage
lsof -i :8000
# Use different port
MCP_PORT=9000 python mcp_launcher.py
```

### Connection refused
```bash
# Verify server is running
ps aux | grep mcp_launcher
# Check firewall/network
ping <dhia-host>
```

### Slow responses
- Check database size: `ls -lh data/chatbot.db`
- Monitor logs during query execution
- Database is indexed for fast lookups

### Test failures
```bash
# Run tests with debug output
python test_mcp.py --host=http://localhost:8000
# Check server logs during test
tail -f mcp_server.log (if enabled)
```

## Deployment

### Local Development
```bash
python mcp_launcher.py
```

### Docker (example)
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "mcp_launcher.py"]
```

### Production
```bash
# Run with process manager (e.g., supervisor, systemd)
MCP_PORT=8000 python mcp_launcher.py
```

## Rollout Checklist

- [ ] Dhia: Start MCP server and verify logs
- [ ] Dhia: Share server URL with Haotian
- [ ] Haotian: Test connection to server
- [ ] Haotian: Discover tools with `tools/list`
- [ ] Haotian: Register server in agent config
- [ ] Haotian: Test `query_platform_supporting` with sample queries
- [ ] Both: Run integration tests in `test_mcp.py`
- [ ] Haotian: Update agent routing logic
- [ ] Both: Deploy to production

## Next Steps

1. **Start the server:** `python mcp_launcher.py`
2. **Run tests:** `python test_mcp.py`
3. **Review documentation:** `docs_md/MCP_SERVER_GUIDE.md`
4. **Integrate with agent:** Follow `MCP_INTEGRATION_SUMMARY.md`
5. **Monitor in production:** Check logs and response times

## References

- [MCP Specification](https://modelcontextprotocol.io)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- Protocol Version: >= 2025-06-18
- Implementation: Python 3.8+

## Support

### For Dhia
- Server implementation: `mcp_server.py`
- Database queries: `database.py`
- Troubleshooting: `docs_md/MCP_SERVER_GUIDE.md`

### For Haotian
- Integration guide: `MCP_INTEGRATION_SUMMARY.md`
- API reference: `docs_md/MCP_SERVER_GUIDE.md`
- Test client: `test_mcp.py`

---

**Project:** dnext-support-chatbot  
**MCP Implementation:** April 2026  
**Status:** Ready for Testing
