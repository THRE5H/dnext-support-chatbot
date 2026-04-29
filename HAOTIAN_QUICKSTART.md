# MCP Server Integration - Haotian's Quick Start Guide

Hi Haotian! 👋 This guide walks you through integrating Dhia's MCP server into your RAG system.

---

## What You're Getting

A **Model Context Protocol (MCP) server** that exposes one tool: **`query_platform_supporting`**

This tool lets your agent query:
- 📊 Platform statistics and analytics
- 👤 User information and lookups
- 💬 Conversation history and records
- 📈 Conversation trends and timeseries data
- 🏥 System health and status

---

## Prerequisites

✅ Network access to Dhia's server  
✅ Your agent supports MCP protocol (≥ 2025-06-18)  
✅ JSON-RPC 2.0 client capability  

---

## Step 1: Get the Server URL

Ask Dhia for the MCP server URL. It will look like:
```
http://<dhia-host>:8000/mcp
```

**For testing locally:**
```
http://localhost:8000/mcp
```

---

## Step 2: Register in Your Agent Config

Update your agent's MCP server configuration file:

### YAML Format
```yaml
mcp_servers:
  platform_supporting:
    transport: streamable_http
    url: http://<dhia-host>:8000/mcp
```

### JSON Format
```json
{
  "mcp_servers": {
    "platform_supporting": {
      "transport": "streamable_http",
      "url": "http://<dhia-host>:8000/mcp"
    }
  }
}
```

### Python Format
```python
mcp_config = {
    'mcp_servers': {
        'platform_supporting': {
            'transport': 'streamable_http',
            'url': 'http://<dhia-host>:8000/mcp'
        }
    }
}
```

---

## Step 3: Test Connection

### Option A: Using the Provided Test Script

```bash
# Get the test script
# Location: test_mcp.py in Dhia's project

# Run tests
python test_mcp.py --host=http://<dhia-host>:8000

# Expected output:
# ✅ Test Suite Complete
# • Tool Discovery: ✓
# • Platform Statistics: ✓
# • User Lookup: ✓
# [...]
```

### Option B: Manual cURL Test

```bash
curl -X POST http://<dhia-host>:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

Expected response: Tool list including `query_platform_supporting`

### Option C: Python Test

```python
import requests
import json

response = requests.post(
    'http://localhost:8000/mcp',
    json={
        'jsonrpc': '2.0',
        'method': 'tools/list',
        'id': 1
    }
)

tools = response.json()['result']['tools']
print(f"Found {len(tools)} tool(s)")
for tool in tools:
    print(f"  - {tool['name']}")
```

---

## Step 4: Discover Tools at Startup

Your agent should make this request at startup to discover available tools:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

Response will include:
- Tool name: `query_platform_supporting`
- Tool description (tells you what it does)
- Input schema (expects a `query` string)

---

## Step 5: Route Platform Queries

Add routing logic in your agent to decide when to use this tool.

### Option A: Simple Keyword Matching

```python
platform_keywords = [
    'statistics', 'metrics', 'total users', 'total conversations',
    'user lookup', 'by email', 'recent conversations',
    'conversation trends', 'analytics', 'system status',
    'health check', 'platform overview'
]

user_query_lower = user_query.lower()
should_use_platform_tool = any(
    keyword in user_query_lower 
    for keyword in platform_keywords
)
```

### Option B: ML-Based Routing

Use your agent's planner to decide:
- Primary data catalog for most queries
- `query_platform_supporting` for platform/analytics questions

### Option C: Update System Prompt

Add this to your agent's system prompt:

```
When the user asks about any of these topics, use the 
query_platform_supporting tool:
- Platform metrics or statistics
- User data or lookups (by email, name, etc.)
- Conversation history or chat records
- Conversation trends or analytics
- System health or performance status

For all other questions, use your primary data catalog.
```

---

## Step 6: Make Tool Calls

When your agent decides to use the tool, send:

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
  "id": 2
}
```

Example requests:
```json
{"query": "show me user statistics"}
{"query": "lookup user john@example.com"}
{"query": "show recent conversations"}
{"query": "conversation trends for last 7 days"}
{"query": "system status"}
```

---

## Step 7: Parse the Response

The server responds with:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"answer\": \"📊 Platform Statistics:\n  • Total Users: 42\n  • Total Conversations: 1,250\n  ...\"}"
    }]
  }
}
```

Parse it:

```python
response = requests.post(...)
data = response.json()
content_text = data['result']['content'][0]['text']
answer = json.loads(content_text)['answer']
print(answer)
```

---

## Example Integration

### User Query
```
"How many users do we have?"
```

### Your Agent's Flow
1. Receives query
2. Recognizes platform-related keywords
3. Calls `query_platform_supporting` tool
4. Receives: "📊 Platform Statistics: Total Users: 42 ..."
5. Returns formatted answer to user

### Full Request/Response

**Your Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "query_platform_supporting",
    "arguments": {
      "query": "how many users do we have?"
    }
  },
  "id": 100
}
```

**Dhia's Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"answer\": \"📊 Platform Statistics:\n  • Total Users: 42\n  • Total Conversations: 1,250\n  • Active Users (last 7 days): 18\n  • Average Response Time: 320ms\"}"
    }]
  }
}
```

**Your Final Answer to User:**
```
📊 Platform Statistics:
  • Total Users: 42
  • Total Conversations: 1,250
  • Active Users (last 7 days): 18
  • Average Response Time: 320ms
```

---

## Supported Query Types

The tool understands these categories naturally:

### 1. Statistics & Metrics
- "show me statistics"
- "platform metrics"
- "system overview"
- "how many users?"
- "total conversations"

### 2. User Lookups
- "lookup user john@example.com"
- "find user by email"
- "show all users"
- "user information"

### 3. Conversation History
- "show recent conversations"
- "get chat history"
- "latest messages"
- "conversation records"

### 4. Analytics & Trends
- "conversation trends for last 7 days"
- "analytics over 14 days"
- "timeseries data"
- "conversation growth"

### 5. System Health
- "system status"
- "is platform healthy?"
- "health check"
- "system performance"

---

## Error Handling

### Connection Refused
```
Error: Connection Error: Cannot reach http://localhost:8000/mcp
Action: Verify Dhia started the server
```

### Timeout
```
Error: Tool call exceeded 60 seconds
Action: Check database performance, reduce query scope
```

### Invalid Tool
```
Error: Unknown tool: query_platform_supporting
Action: Verify tool name spelling, rediscover tools
```

### Malformed Request
```
Error: Invalid JSON in request
Action: Validate request format matches JSON-RPC 2.0
```

---

## Performance Expectations

- ✅ Typical response: < 2 seconds
- ✅ Maximum response: 60 seconds (guaranteed)
- ✅ Concurrent requests: Supported
- ✅ Availability: 99% (internal network)

---

## Debugging Checklist

If integration isn't working:

- [ ] Can I reach the server? (ping, telnet, curl)
- [ ] Is the server running? (check with Dhia)
- [ ] Is my MCP config correct? (check YAML syntax)
- [ ] Can I list tools? (try tools/list request)
- [ ] Are my requests JSON-RPC 2.0 format?
- [ ] Am I parsing responses correctly?
- [ ] Check server logs (ask Dhia for logs)

---

## Common Questions

**Q: Do I need authentication?**  
A: No, it's internal network only.

**Q: What if the server goes down?**  
A: Implement fallback logic to skip platform queries.

**Q: Can I cache responses?**  
A: Yes, statistics change infrequently. Use short TTL cache.

**Q: What about slow networks?**  
A: Server has 60-second timeout, adjust as needed.

**Q: Can I modify tool behavior?**  
A: No, ask Dhia for changes (edit mcp_server.py).

---

## Next Steps

1. ✅ Get server URL from Dhia
2. ✅ Test connection: `curl -X POST http://<url> ...`
3. ✅ Register in agent config
4. ✅ Discover tools: `tools/list`
5. ✅ Add routing logic to your agent
6. ✅ Test with sample queries
7. ✅ Deploy to production
8. ✅ Monitor in production

---

## Documentation Links

- **API Reference:** `docs_md/MCP_SERVER_GUIDE.md`
- **Quick Reference:** `MCP_INTEGRATION_SUMMARY.md`
- **Project Overview:** `MCP_README.md`
- **Implementation Report:** `MCP_IMPLEMENTATION.md`
- **Test Script:** `test_mcp.py`

---

## Example Code (JavaScript/Node.js)

```javascript
// Discover tools
const toolsResponse = await fetch('http://localhost:8000/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/list',
    id: 1
  })
});

// Query the tool
const queryResponse = await fetch('http://localhost:8000/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'query_platform_supporting',
      arguments: {
        query: 'show me system statistics'
      }
    },
    id: 2
  })
});

const data = await queryResponse.json();
const answer = JSON.parse(
  data.result.content[0].text
).answer;

console.log(answer);
```

---

## Example Code (Python)

```python
import requests
import json

class MCPClient:
    def __init__(self, url):
        self.url = url
        self.request_id = 0
    
    def _get_id(self):
        self.request_id += 1
        return self.request_id
    
    def list_tools(self):
        response = requests.post(self.url, json={
            'jsonrpc': '2.0',
            'method': 'tools/list',
            'id': self._get_id()
        })
        return response.json()
    
    def query(self, question):
        response = requests.post(self.url, json={
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': 'query_platform_supporting',
                'arguments': {'query': question}
            },
            'id': self._get_id()
        })
        data = response.json()
        content = data['result']['content'][0]['text']
        answer = json.loads(content)['answer']
        return answer

# Usage
client = MCPClient('http://localhost:8000/mcp')
print(client.query('show me system statistics'))
```

---

## Support

For issues or questions:
- **Dhia:** Server side problems
- **Haotian (You):** Integration and routing
- **Both:** Check documentation first

---

**Status:** Ready to integrate  
**Test:** Run `python test_mcp.py`  
**Deploy:** Follow production checklist  

Good luck! 🚀
