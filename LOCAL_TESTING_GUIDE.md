# MCP Server Local Testing Guide

Before deploying to Railway and sharing with Haotian, test everything locally.

## Prerequisites

- Backend running: `cd backend && python main.py`
- MCP server dependencies installed: `pip install -r backend/mcp_spec_server/requirements.txt`

---

## Step 1: Start the MCP Server

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
```
Wait for: `Application startup complete`

**Terminal 2 (MCP Server):**
```bash
cd backend/mcp_spec_server
python http_server.py
```

Expected output:
```
[MCP] MCP Server initialized
[MCP] Starting HTTP server on 0.0.0.0:8001
Server running on http://0.0.0.0:8001
```

---

## Step 2: Test with cURL (Easiest)

**Test 1: Check Health**
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{"status":"ok","message":"MCP server is healthy"}
```

**Test 2: List Tools**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

Expected response includes `query_platform_supporting` tool definition.

**Test 3: Query Platform Question (GOOD - should answer)**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "What is DNEXT platform?"
      }
    }
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"DNEXT platform is...\"}"
      }
    ]
  }
}
```

**Test 4: Query Data Question (SHOULD REDIRECT)**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "What are the sales figures for Q3?"
      }
    }
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"That's a data-specific question...\"}"
      }
    ]
  }
}
```

---

## Step 3: Test with Python Script

**Create test_local.py:**
```python
import json
import requests

MCP_URL = "http://localhost:8001/mcp"

def test_list_tools():
    """Test listing available tools"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    response = requests.post(MCP_URL, json=payload)
    print("[TEST] List Tools:")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert "query_platform_supporting" in str(response.json())
    print("✅ PASS\n")

def test_platform_question():
    """Test platform documentation question"""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "query_platform_supporting",
            "arguments": {
                "query": "How does authentication work in DNEXT?"
            }
        }
    }
    response = requests.post(MCP_URL, json=payload)
    print("[TEST] Platform Question:")
    result = response.json()
    print(json.dumps(result, indent=2))
    assert response.status_code == 200
    assert "answer" in str(result)
    print("✅ PASS\n")

def test_data_question():
    """Test data question (should be redirected)"""
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "query_platform_supporting",
            "arguments": {
                "query": "Show me customer sales data"
            }
        }
    }
    response = requests.post(MCP_URL, json=payload)
    print("[TEST] Data Question (should redirect):")
    result = response.json()
    print(json.dumps(result, indent=2))
    assert response.status_code == 200
    assert "data" in str(result).lower() or "catalog" in str(result).lower()
    print("✅ PASS (correctly redirected)\n")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP SERVER LOCAL TESTING")
    print("=" * 60 + "\n")
    
    try:
        test_list_tools()
        test_platform_question()
        test_data_question()
        print("=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
```

**Run it:**
```bash
cd backend/mcp_spec_server
python test_local.py
```

---

## Step 4: Test with MCP Inspector (Optional)

If you have MCP Inspector installed:

```bash
# Install MCP Inspector (if not already)
npm install -g @modelcontextprotocol/inspector

# Connect to your local server
mcp-inspector http://localhost:8001/mcp
```

This opens a GUI where you can:
1. See the tool definition
2. Test queries interactively
3. See full request/response

---

## Validation Checklist

Before sending to Haotian, verify:

- [x] Health endpoint responds with `status: ok`
- [x] `tools/list` returns `query_platform_supporting` tool
- [x] Platform questions get answered with `{"answer": "..."}`
- [x] Data questions get redirected with clear message
- [x] No error messages or stack traces exposed
- [x] Response time is < 60 seconds
- [x] All responses use correct JSON-RPC format
- [x] Server handles concurrent requests

---

## Common Issues

**Issue: Connection refused**
```
Solution: Make sure both backend and MCP server are running
```

**Issue: Tool not found**
```
Solution: Check http_server.py - tools/list might need updating
```

**Issue: Timeout (>60s)**
```
Solution: Backend might be slow. Check backend logs
```

**Issue: Wrong response format**
```
Solution: Verify tools.py returns {"answer": "..."} format
```

---

## What to Verify

1. ✅ Server starts without errors
2. ✅ Health check passes
3. ✅ Tool is discoverable
4. ✅ Platform questions answered correctly
5. ✅ Data questions redirected properly
6. ✅ Response format is exact JSON
7. ✅ Performance is acceptable

**Once all tests pass, you're ready to deploy to Railway!**
