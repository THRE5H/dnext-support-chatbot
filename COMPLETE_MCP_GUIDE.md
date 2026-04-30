# Complete MCP Server Guide: From Testing to Production

This guide covers everything: local testing, Railway deployment, and sharing with Haotian.

---

## Overview

You have:
- ✅ MCP server implementation (`backend/mcp_spec_server/`)
- ✅ Local testing setup
- ✅ Railway deployment ready
- ✅ Documentation for Haotian

---

## Part 1: Local Testing (Before Deployment)

### 1.1 Start the Services

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```
Wait for: `Application startup complete`

**Terminal 2 - MCP Server:**
```bash
cd backend/mcp_spec_server
python http_server.py
```
Expected: `Server running on http://0.0.0.0:8001`

### 1.2 Quick Tests

**Test 1: Health Check**
```bash
curl http://localhost:8001/health
# Response: {"status":"ok","message":"MCP server is healthy"}
```

**Test 2: List Tools**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

**Test 3: Query Platform (should answer)**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {"query": "What is DNEXT platform?"}
    }
  }'
# Response includes: {"answer": "DNEXT platform is..."}
```

**Test 4: Query Data (should redirect)**
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {"query": "Show Q3 sales data"}
    }
  }'
# Response includes: {"answer": "That's a data-specific question..."}
```

### 1.3 Run Test Suite

```bash
python backend/mcp_spec_server/test_mcp.py
```

Expected output:
```
═════════════════════════════════════════════
           ALL TESTS PASSED ✅
═════════════════════════════════════════════
```

---

## Part 2: Railway Deployment (Production URL)

Once local testing is done, deploy to Railway for a production URL.

### 2.1 Prepare Files (One-time)

These files should already exist, just verify:

**File: `Procfile` (project root)**
```
mcp: cd backend/mcp_spec_server && python http_server.py
```

**File: `railway.json` (project root)**
```json
{
  "build": {
    "builder": "dockerfile",
    "context": "./backend/mcp_spec_server"
  },
  "deploy": {
    "startCommand": "python http_server.py"
  }
}
```

**File: `backend/mcp_spec_server/Dockerfile`** (already exists)

### 2.2 Push to GitHub

```bash
git add .
git commit -m "Add MCP server with Railway deployment"
git push origin main
```

### 2.3 Deploy on Railway

1. Go to https://railway.app
2. Sign up (free)
3. Click "New Project"
4. Select "GitHub Repo"
5. Connect your GitHub account
6. Select `dnext-support-chatbot` repository
7. Railway auto-detects and deploys (2-3 minutes)

### 2.4 Configure Environment Variables

In Railway dashboard:
1. Click your project
2. Go to "Variables" tab
3. Add:
   ```
   BACKEND_URL=http://localhost:8000
   (or your actual backend service URL)
   
   MCP_SERVER_HOST=0.0.0.0
   MCP_SERVER_PORT=8001
   ```

### 2.5 Get Your Production URL

1. Go to Deployments tab
2. Find "mcp-server" service
3. Copy the URL: `https://xxxx.up.railway.app`

**Your production endpoint: `https://xxxx.up.railway.app/mcp`**

### 2.6 Test Production URL

```bash
# Health check
curl https://xxxx.up.railway.app/health

# List tools
curl -X POST https://xxxx.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# Query platform (test)
curl -X POST https://xxxx.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "query_platform_supporting",
      "arguments": {"query": "How does authentication work?"}
    }
  }'
```

---

## Part 3: Share with Haotian

Once production testing passes, send Haotian this email:

---

### Email to Haotian

**Subject:** DNEXT MCP Server Ready for Integration

Dear Haotian,

The DNEXT MCP server is ready for integration. Here are the details:

**Endpoint:**
```
https://xxxx.up.railway.app/mcp
```

**Tool Definition (add to your agent config):**
```json
{
  "name": "query_platform_supporting",
  "description": "This agent answers platform-related questions about the DNEXT platform: module definitions, feature explanations, how-to guides, general troubleshooting, user documentation, and support email knowledge. It does NOT answer questions about specific datasets, data values, metadata, catalogue entries, or anything requiring SQL execution. Call this tool when the user asks how something works, what something means, or how to fix a general platform issue.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" }
    },
    "required": ["query"]
  }
}
```

**Example Request (Platform Question):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_platform_supporting",
    "arguments": {
      "query": "How do I configure authentication in DNEXT?"
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"To configure authentication in DNEXT, you need to...\"}"
      }
    ]
  }
}
```

**Example: Data Question (redirected):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "query_platform_supporting",
    "arguments": {
      "query": "What are the Q3 sales figures?"
    }
  }
}
```

**Response (redirected):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"That's a data-specific question. Please use the data-catalog tool or query_data tool instead.\"}"
      }
    ]
  }
}
```

The server is production-ready and fully tested. Responses are guaranteed within 60 seconds.

Let me know if you need any assistance with integration.

Best regards,
[Your Name]

---

---

## Troubleshooting

### Local Testing Issues

**Port 8001 already in use:**
```bash
# Find what's using port 8001
lsof -i :8001

# Kill it or use different port
MCP_SERVER_PORT=8002 python http_server.py
```

**Backend connection error:**
```bash
# Make sure backend is running
# Check BACKEND_URL in config.py or .env file
# Default: http://localhost:8000
```

**Timeout (>60s):**
```bash
# Backend might be slow
# Check backend logs
# Try backend health check: curl http://localhost:8000/api/health
```

### Railway Issues

**Build fails:**
- Check Dockerfile syntax
- Verify requirements.txt exists
- View logs: Click "Deployments" → "Build Logs"

**Service won't start:**
- Check environment variables are set
- View service logs: `railway logs -s mcp-server`
- Verify http_server.py exists in Docker context

**Timeout from Railway:**
- BACKEND_URL might be wrong
- Set BACKEND_URL to actual backend service
- Check network connectivity between services

---

## Documentation Files

| File | Purpose |
|------|---------|
| `LOCAL_TESTING_GUIDE.md` | Detailed local testing procedures |
| `RAILWAY_DEPLOYMENT.md` | Step-by-step Railway setup |
| `HAOTIAN_INTEGRATION.md` | Integration guide for Haotian |
| `TEST_AND_DEPLOY.txt` | Quick reference card |
| `backend/mcp_spec_server/README.md` | Server technical details |

---

## Quick Checklist

### Before Deploying to Railway
- [ ] Backend starts: `python main.py`
- [ ] MCP server starts: `python http_server.py`
- [ ] Health check passes: `curl http://localhost:8001/health`
- [ ] Tool discovery works
- [ ] Platform questions answered
- [ ] Data questions redirected
- [ ] test_mcp.py passes all tests

### After Railway Deployment
- [ ] Production URL accessible
- [ ] Health check passes on production
- [ ] Tool discovery works on production
- [ ] Platform questions answered on production
- [ ] Data questions redirected on production
- [ ] Response time acceptable

### Before Sending to Haotian
- [ ] All production tests pass
- [ ] Email with endpoint and tool definition ready
- [ ] Example requests/responses included
- [ ] Haotian has integration guide

---

## You're All Set!

You now have:
✅ A local MCP server running on localhost:8001  
✅ A production MCP server on Railway (https://xxxx.up.railway.app)  
✅ Full testing coverage  
✅ Documentation for Haotian  

Send Haotian the endpoint and he can start using it immediately!

---

**Questions?** Check the documentation files above or review the code in `backend/mcp_spec_server/`.
