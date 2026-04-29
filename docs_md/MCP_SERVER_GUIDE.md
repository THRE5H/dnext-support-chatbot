# MCP Server Integration Guide

## Overview

This guide documents the Model Context Protocol (MCP) server that exposes Dhia's platform database to Haotian's RAG system. It provides a single tool: **`query_platform_supporting`**.

**Key Info:**
- **Protocol:** MCP (Model Context Protocol) version >= 2025-06-18
- **Transport:** HTTP/JSON-RPC 2.0 over streamable HTTP
- **Authentication:** None (internal network only)
- **Tool:** `query_platform_supporting` — Query platform data and analytics

---

## Architecture

```
Haotian's RAG Agent (MCP Client)
         ↓
    (POST /mcp)
         ↓
Dhia's MCP Server (this project)
         ↓
    Database + Auth Service
         ↓
    SQLite Database (chatbot.db)
```

No shared database. Communication is JSON-RPC only.

---

## Starting the MCP Server

### Option 1: Run Standalone (Recommended for Testing)

```bash
python mcp_launcher.py
```

Server starts on `http://0.0.0.0:8000/mcp`

Environment variable override:
```bash
MCP_PORT=9000 python mcp_launcher.py
```

### Option 2: Run as Subprocess from main.py

Edit `main.py` to start MCP server in background:
```python
import threading
from mcp_server import start_mcp_server

# In main():
mcp_thread = threading.Thread(
    target=start_mcp_server,
    args=(8000, db, auth),
    daemon=True
)
mcp_thread.start()

# Then continue with Gradio app
app = ChatbotApp(db, auth)
...
```

---

## API Specification

### Endpoint

```
POST http://<host>:8000/mcp
Content-Type: application/json
```

### Request Format (JSON-RPC 2.0)

#### List Tools

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
        "description": "Query Dhia's platform database...",
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

#### Call Tool

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

---

## Tool Description

The `query_platform_supporting` tool answers these categories of questions:

### ✅ Supported Queries

1. **User Statistics & Analytics**
   - "show me user statistics"
   - "what are system metrics?"
   - "total number of users"

2. **User Lookups**
   - "lookup user john@example.com"
   - "find user by email"
   - "show all users"

3. **Conversation History**
   - "show recent conversations"
   - "get chat history"
   - "conversation records"

4. **Timeseries Analytics**
   - "conversation trends for the last 7 days"
   - "analytics over 14 days"
   - "timeseries data"

5. **System Health**
   - "system status"
   - "is the system healthy?"
   - "platform health check"

### ❌ NOT Supported

- Technical troubleshooting
- AI model decisions or reasoning
- Product-specific feature questions
- Real-time chat/conversation conduct

---

## Integration with Haotian's System

### Step 1: Get MCP Server URL

From Dhia:
```
http://<your-host>:8000/mcp
```

Example (for testing):
```
http://localhost:8000/mcp
```

### Step 2: Register in Agent Config

Update Haotian's MCP server configuration file (e.g., `mcp_config.yaml`):

```yaml
mcp_servers:
  platform_supporting:
    transport: streamable_http
    url: http://<dhia-host>:8000/mcp
```

### Step 3: Discover Tools at Startup

Haotian's agent should send `tools/list` request to discover available tools.

### Step 4: Update System Prompt

Add routing logic in Haotian's system prompt:

```
When the user asks about platform metrics, user data, conversation history, 
or system analytics, prefer the query_platform_supporting tool from Dhia's 
platform supporting agent. Use your primary data catalog for all other queries.
```

### Step 5: Call the Tool

When Haotian's planner decides to use the tool:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "query_platform_supporting",
    "arguments": {
      "query": "<user's question about platform data>"
    }
  },
  "id": <request_id>
}
```

---

## Example Workflows

### Query 1: Get System Overview

**Request:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "show me system statistics"
      }
    },
    "id": 1
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
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

### Query 2: Lookup User

**Request:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "lookup user john.doe@example.com"
      }
    },
    "id": 2
  }'
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
        "text": "{\"answer\": \"👤 User Information:\n  • Name: John Doe\n  • Email: john.doe@example.com\n  • Status: active\n  • Total Queries: 45\n  • Created: 2024-03-15 10:30:00\n  • Last Login: 2024-04-28 14:22:00\"}"
      }
    ]
  }
}
```

### Query 3: Get Conversation Trends

**Request:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "show conversation trends for the last 7 days"
      }
    },
    "id": 3
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"📈 Conversation Trend (Last 7 days):\n  2024-04-22: 120 conversations\n  2024-04-23: 145 conversations\n  2024-04-24: 135 conversations\n  2024-04-25: 160 conversations\n  2024-04-26: 150 conversations\n  2024-04-27: 175 conversations\n  2024-04-28: 140 conversations\n  Total: 1,025 conversations\"}"
      }
    ]
  }
}
```

---

## Error Handling

### Bad Request (Invalid Tool Name)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Unknown tool: invalid_tool"
  }
}
```

### Internal Server Error

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error: Database connection failed"
  }
}
```

### Malformed Request

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32700,
    "message": "Parse error"
  }
}
```

---

## Performance & Reliability

### Response Time Guarantee

- Query execution: **< 60 seconds**
- Typical response: **< 2 seconds**

### Logs

Monitor server logs:
```bash
tail -f mcp_server.log
```

Each request is logged with timestamp and execution time.

### Health Check

Send a `tools/list` request to verify the server is responsive.

---

## Security Notes

⚠️ **Important:**
- No authentication (assumes internal network)
- Should only be exposed within trusted infrastructure
- For production: Add API key authentication if exposed to external networks
- Database contains user conversation history—handle with care

---

## Troubleshooting

### Server won't start

```bash
# Check if port 8000 is in use
netstat -tuln | grep 8000

# Use different port
MCP_PORT=9000 python mcp_launcher.py
```

### Slow responses

Check database performance:
```bash
# Review SQLite database size
ls -lh data/chatbot.db
```

### Connection refused

Verify server is running:
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

---

## References

- [MCP (Model Context Protocol) Spec](https://modelcontextprotocol.io)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- Project Database: `database.py`
- Agent Implementation: `mcp_server.py`

---

## Contact

For questions or issues:
- Dhia: Implementation & Database
- Haotian: Integration & Agent Configuration
