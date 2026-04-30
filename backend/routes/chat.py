"""Chat endpoint with streaming support"""

import logging
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional

from schemas.messages import ChatRequest, ErrorResponse
from services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()
chat_service = ChatService()


def generate_sse_stream(message: str, session_id: Optional[str] = None, files: list = None):
    """Generate Server-Sent Events stream for chat response"""
    try:
        for chunk in chat_service.stream_chat_response(message, session_id, files):
            # Format as SSE
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        logger.error(f"Error in SSE stream: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint with streaming response.
    
    Returns Server-Sent Events stream of response chunks.
    """
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")
        
        # Generate SSE stream
        return StreamingResponse(
            generate_sse_stream(
                message=request.message,
                session_id=request.session_id,
                files=None,  # File upload via multipart in separate endpoint
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/chat/with-files")
async def chat_with_files(
    message: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    files: list[UploadFile] = File(None),
):
    """
    Chat endpoint with file upload support.
    
    Accepts multipart/form-data with optional files.
    """
    try:
        if not message and not files:
            raise HTTPException(
                status_code=400,
                detail="Either message or files must be provided",
            )
        
        logger.info(f"Processing chat with files: {message[:50] if message else 'no text'}... ({len(files or [])} files)")
        
        # Convert uploaded files to file paths for V1 processing
        file_paths = []
        if files:
            for file in files:
                # TODO: Save uploaded files temporarily and pass to handler
                file_paths.append(file.filename)
        
        # Generate SSE stream
        return StreamingResponse(
            generate_sse_stream(
                message=message or "",
                session_id=session_id,
                files=file_paths,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
    
    except Exception as e:
        logger.error(f"Error in chat_with_files endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    session = chat_service.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "messages": session.messages,
        "created_at": session.created_at,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Clear a session"""
    if chat_service.clear_session(session_id):
        return {"message": f"Session {session_id} cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")
