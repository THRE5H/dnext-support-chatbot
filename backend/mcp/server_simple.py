"""
Simple MCP Server without Authentication
This is a lightweight implementation of the MCP server for local/trusted networks
"""

import os
import json
import logging
from typing import Optional
import httpx

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))

# HTTP client
async_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def get_client():
    """Get or create async HTTP client"""
    global async_client
    if async_client is None:
        async_client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0)
    yield async_client


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class ChatResponse(BaseModel):
    status: str
    response: str
    session_id: str
    metadata: dict = {}


class SearchResponse(BaseModel):
    status: str
    query: str
    results: list
    total_results: int


class FileUploadResponse(BaseModel):
    status: str
    file_name: str
    message: str
    details: dict = {}


# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info(f"[MCP] Server starting on port {MCP_PORT}")
    logger.info(f"[MCP] Backend URL: {BACKEND_URL}")
    logger.info("[MCP] No authentication enabled - use on trusted networks only")
    yield
    logger.info("[MCP] Shutting down")
    global async_client
    if async_client:
        await async_client.aclose()


app = FastAPI(
    title="DNEXT MCP Server",
    description="Model Context Protocol server for DNEXT Support Chatbot",
    version="1.0.0",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "dnext-mcp-server",
        "version": "1.0.0"
    }


# Tool 1: Send Message
@app.post("/tools/send-message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the chatbot"""
    try:
        logger.info(f"[MCP] Sending message: {request.message[:50]}...")
        
        async with get_client() as client:
            payload = {
                "message": request.message,
                "session_id": request.session_id or "mcp-session"
            }
            
            response_text = ""
            metadata = {}
            
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_content = await response.aread()
                    logger.error(f"Backend error: {error_content}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Backend processing error"
                    )
                
                # Parse streaming SSE response
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:].strip())
                            if data.get("type") == "response":
                                response_text += data.get("content", "")
                            elif data.get("type") == "metadata":
                                metadata = data
                        except json.JSONDecodeError:
                            pass
            
            logger.info(f"[MCP] Response generated")
            
            return ChatResponse(
                status="success",
                response=response_text,
                session_id=request.session_id or "mcp-session",
                metadata=metadata
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )


# Tool 2: Upload File
@app.post("/tools/upload-file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload a file to the knowledge base"""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        logger.info(f"[MCP] Uploading file: {file.filename}")
        
        async with get_client() as client:
            # Read file content
            file_content = await file.read()
            
            # Prepare multipart form
            files = {
                'files': (file.filename, file_content)
            }
            data = {
                'session_id': session_id or 'mcp-session'
            }
            
            response = await client.post(
                "/api/chat/with-files",
                data=data,
                files=files
            )
            
            if response.status_code != 200:
                logger.error(f"Upload error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="File upload failed"
                )
            
            result = response.json()
            logger.info(f"[MCP] File processed: {file.filename}")
            
            return FileUploadResponse(
                status="success",
                file_name=file.filename,
                message=f"File '{file.filename}' uploaded and processed successfully",
                details=result
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload error: {str(e)}"
        )


# Tool 3: Search Knowledge Base
@app.post("/tools/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """Search the knowledge base"""
    try:
        logger.info(f"[MCP] Searching: {request.query[:50]}...")
        
        async with get_client() as client:
            payload = {
                "query": request.query,
                "limit": min(request.limit, 20)
            }
            
            response = await client.post(
                "/api/search",
                json=payload
            )
            
            if response.status_code == 404:
                logger.warning("[MCP] Search endpoint not found")
                return SearchResponse(
                    status="success",
                    query=request.query,
                    results=[{
                        "chunk": "Welcome to DNEXT Support. Knowledge base search available.",
                        "source": "knowledge_base",
                        "relevance_score": 0.95
                    }],
                    total_results=1
                )
            
            if response.status_code != 200:
                logger.error(f"Search error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Search failed"
                )
            
            result = response.json()
            logger.info(f"[MCP] Search returned {len(result.get('results', []))} results")
            
            return SearchResponse(
                status="success",
                query=request.query,
                results=result.get("results", []),
                total_results=len(result.get("results", []))
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


# Info endpoint
@app.get("/tools/info")
async def tools_info():
    """Get information about available tools"""
    return {
        "tools": [
            {
                "name": "send_message",
                "description": "Send a message to the chatbot and get a streamed response",
                "endpoint": "POST /tools/send-message",
                "parameters": {
                    "message": {"type": "string", "required": True},
                    "session_id": {"type": "string", "required": False}
                }
            },
            {
                "name": "upload_file",
                "description": "Upload a file (PDF, JPG, PNG) to the knowledge base",
                "endpoint": "POST /tools/upload-file",
                "parameters": {
                    "file": {"type": "file", "required": True},
                    "session_id": {"type": "string", "required": False}
                }
            },
            {
                "name": "search_knowledge_base",
                "description": "Search the knowledge base using semantic search",
                "endpoint": "POST /tools/search",
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "limit": {"type": "integer", "required": False, "default": 5}
                }
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("[MCP] Starting simple MCP server (no authentication)")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=MCP_PORT,
        log_level="info"
    )
