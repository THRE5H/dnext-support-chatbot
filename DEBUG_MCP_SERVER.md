# Debugging MCP Server - Response Parsing Fix

## What Was Wrong

The MCP server was receiving a 200 status from the backend but returning a generic error: "I encountered an unexpected error. Please rephrase your question."

**Root Cause**: The response parsing logic wasn't handling the backend's response format correctly.

## What I Fixed

Updated `backend/mcp_spec_server/tools.py`:

1. **Better Error Logging**: Now logs the backend URL and status code
2. **Improved Response Parsing**: Handles both JSON and streaming (SSE) responses
3. **Multiple Fallbacks**: Tries JSON first, then streaming, then raw text
4. **Debug Information**: Error messages now include context about what failed

## How to Test Now

### Step 1: Verify Backend is Running

```bash
curl http://localhost:8000/api/health
# Should return: {"status":"ok"}
```

### Step 2: Restart MCP Server

```bash
cd backend/mcp_spec_server
python http_server.py
```

Watch the logs - you should see:
```
[MCP HTTP] Starting server on 0.0.0.0:8001
[MCP HTTP] Endpoint: http://0.0.0.0:8001/mcp
```

### Step 3: Run Tests (with more debug output)

```bash
python backend/mcp_spec_server/test_mcp.py
```

Now you should see detailed logs showing:
- Backend URL being called
- Response status code
- How the response is being parsed
- Any errors with full tracebacks

### Step 4: Manual cURL Test

```bash
# Test platform documentation question
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {
        "query": "What is DNEXT?"
      }
    }
  }'
```

You should get a response with the actual answer, not an error.

## Expected Behavior Now

**Platform Question**: 
- Input: "How do I configure authentication?"
- Output: Actual answer from backend (e.g., "To configure authentication...")

**Data Question**:
- Input: "What are the sales figures?"
- Output: "That's a data-specific question. Please use the data-catalog tool instead."

**Error Cases**:
- Backend not running: Error mentions `http://localhost:8000/api/chat` 
- Invalid query: Proper error from backend, not generic message

## Troubleshooting

### If you see: "Backend error: 500"

**Problem**: Backend endpoint is throwing an error
**Solution**: 
1. Check if backend `/api/chat` endpoint is working: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message": "test"}'`
2. Check backend logs for actual error
3. Ensure all backend dependencies are installed

### If you see: "Error: Unknown tool"

**Problem**: Tool name mismatch
**Solution**: Check that tool name in request is exactly `query_platform_supporting`

### If you see: "Backend error: Connection refused"

**Problem**: Backend isn't running
**Solution**: 
1. Make sure backend is running on port 8000
2. Check: `lsof -i :8000` (or `netstat -ano | findstr :8000` on Windows)

### If tests pass but curl fails

**Problem**: Different content types or formatting
**Solution**: Try the test Python script instead, it handles all details

## What Changed in the Code

### In `tools.py`:

**Before**: Generic catch-all errors, poor response parsing

**After**:
- Logs backend URL and status code for debugging
- Tries JSON parsing first (most backends return JSON)
- Falls back to streaming (SSE) parsing
- Falls back to raw text
- Includes error context: what backend URL, what failed, why

### Example Error Messages Now:
- ✅ "Backend error: 500. Please check if the DNEXT backend is running."
- ✅ "Error: Connection refused. Make sure backend is running at http://localhost:8000/api/chat"
- ✅ "Error parsing response: json.JSONDecodeError(...). Raw response was: ..."

Instead of:
- ❌ "I encountered an unexpected error. Please rephrase your question."

## Next Steps

1. Run the test with the fixed code: `python backend/mcp_spec_server/test_mcp.py`
2. Check the logs - they will tell you exactly what's happening
3. If backend integration still fails, let me know the error details from the logs
4. Once local tests pass, proceed to Railway deployment

## For Railway Deployment

Once local testing works, deployment is straightforward:
1. The fixed code will work the same on Railway
2. Just ensure `BACKEND_URL` environment variable points to your DNEXT backend
3. Everything else is automatic

