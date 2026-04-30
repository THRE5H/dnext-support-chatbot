# Deploy MCP Server to Railway (Production Ready)

Railway is perfect for deploying your MCP server. You'll get a production-ready URL like `https://dnext-mcp-production.up.railway.app/mcp`

---

## Prerequisites

1. Railway account: https://railway.app (sign up free)
2. Your code on GitHub (public or private)
3. Backend service running (needed for MCP to call)

---

## Step 1: Prepare for Railway

### 1.1 Create Procfile (tells Railway how to start the server)

**Create file: `Procfile` at project root**

```
mcp: cd backend/mcp_spec_server && python http_server.py
```

### 1.2 Create railway.json (Railway configuration)

**Create file: `railway.json` at project root**

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

### 1.3 Update Dockerfile

**File: `backend/mcp_spec_server/Dockerfile`** (already exists, just verify):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY . .

# Expose port
EXPOSE 8001

# Start server
CMD ["python", "http_server.py"]
```

### 1.4 Update requirements.txt

**File: `backend/mcp_spec_server/requirements.txt`**

Make sure it includes:
```
mcp>=0.1.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
requests>=2.31.0
```

---

## Step 2: Set Up Railway Project

### 2.1 Connect GitHub

1. Go to https://railway.app
2. Click "New Project"
3. Select "GitHub Repo" 
4. Connect your GitHub account
5. Select your `dnext-support-chatbot` repository

### 2.2 Configure Environment Variables

Once repo is connected:

1. Click on your project
2. Go to "Variables" tab
3. Add these environment variables:

```
BACKEND_URL=http://your-backend-service:8000
(or if backend is on same Railway: http://backend-service-name:8000)

MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8001
```

### 2.3 Configure Service

1. Go to "Services"
2. Click "Add Service"
3. Select "Docker" 
4. Set name: `mcp-server`
5. Set Port: `8001`

---

## Step 3: Deploy

### Option A: Deploy from GitHub

1. Push your code to GitHub:
```bash
git add .
git commit -m "Add MCP server"
git push origin main
```

2. Railway automatically deploys from GitHub

3. Wait for deployment to complete (2-3 minutes)

### Option B: Deploy with Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create/link project
railway init

# Deploy
railway up
```

---

## Step 4: Get Your Production URL

Once deployed:

1. Go to Railway dashboard
2. Click your project
3. Go to "Deployments"
4. Find the "MCP Server" service
5. Copy the URL: `https://xxxx.up.railway.app`

**Your production URL is: `https://xxxx.up.railway.app/mcp`**

---

## Step 5: Test Production URL

### Test 1: Health Check
```bash
curl https://xxxx.up.railway.app/health
```

### Test 2: List Tools
```bash
curl -X POST https://xxxx.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Test 3: Query Tool
```bash
curl -X POST https://xxxx.up.railway.app/mcp \
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

---

## Step 6: Share with Haotian

Send Haotian:

**Email:**
```
Hi Haotian,

MCP Server is ready for integration. Here are the details:

Endpoint: https://xxxx.up.railway.app/mcp

Tool Definition:
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

Example Request:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_platform_supporting",
    "arguments": {
      "query": "How do I configure authentication?"
    }
  }
}

Example Response:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"To configure authentication, you...\"}"
      }
    ]
  }
}

Ready to integrate!
```

---

## Step 7: Monitor in Production

### View Logs
```bash
railway logs -s mcp-server
```

### View Metrics
In Railway dashboard → Metrics tab:
- Requests/second
- Response time
- Errors
- Memory usage

### Environment Variables
If you need to update config:
1. Go to Variables tab
2. Edit and save
3. Railway auto-redeploys

---

## Architecture on Railway

```
┌─────────────────────────────────────┐
│     Haotian's Agent                 │
└────────────┬────────────────────────┘
             │ HTTP POST
             ▼
┌─────────────────────────────────────┐
│  Railway MCP Server Service         │
│  https://xxxx.up.railway.app/mcp    │
└────────────┬────────────────────────┘
             │ Calls
             ▼
┌─────────────────────────────────────┐
│  Your Backend (/api/chat)           │
│  (via BACKEND_URL env var)          │
└─────────────────────────────────────┘
```

---

## Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Verify requirements.txt is present
- Check logs in Railway dashboard

### Service Won't Start
- Verify `http_server.py` exists
- Check environment variables
- View Railway logs: `railway logs`

### Timeout Errors
- MCP server might be waiting for backend
- Ensure BACKEND_URL is correct
- Check backend service is accessible

### Slow Responses
- Check Railway metrics for CPU/memory
- Upgrade Railway plan if needed
- Optimize backend response time

---

## Cost

Railway free tier includes:
- 5GB disk
- 512MB RAM
- $5 credit/month
- Perfect for testing

For production, consider upgrading to paid plan (~$5-10/month per service).

---

## Summary

✅ Local testing done  
✅ Code pushed to GitHub  
✅ Railway project created  
✅ Environment variables configured  
✅ Deployment successful  
✅ Production URL working  
✅ Shared with Haotian  

You now have a **production-ready MCP server** that Haotian can integrate with!
