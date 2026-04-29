"""Tool implementations for MCP server."""
import asyncio
import json
import logging
from typing import Any, Dict
import httpx

from config import (
    BACKEND_CHAT_ENDPOINT,
    SYSTEM_PROMPT,
    RESPONSE_TIMEOUT,
    TOOL_NAME,
    TOOL_DESCRIPTION,
)

logger = logging.getLogger(__name__)


class QueryPlatformSupportingTool:
    """Implementation of query_platform_supporting tool."""

    def __init__(self):
        self.name = TOOL_NAME
        self.description = TOOL_DESCRIPTION
        self.input_schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

    async def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the query against the platform support agent.

        Args:
            query: The user's question about DNEXT platform

        Returns:
            Dict with "answer" key containing the response
        """
        try:
            logger.info(f"[MCP Tool] Processing query: {query[:100]}...")

            # Call backend /api/chat endpoint with system prompt
            async with httpx.AsyncClient(timeout=RESPONSE_TIMEOUT) as client:
                response = await client.post(
                    BACKEND_CHAT_ENDPOINT,
                    json={
                        "message": query,
                        "session_id": "mcp_platform_support",
                        # The system prompt is injected in the message context
                        "system_context": SYSTEM_PROMPT,
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"[MCP Tool] Backend error: {response.status_code} - {response.text}"
                    )
                    return {
                        "answer": "I encountered an error processing your question. Please try again."
                    }

                # Parse streaming response
                response_text = await self._parse_streaming_response(
                    response, client, BACKEND_CHAT_ENDPOINT, query
                )

                logger.info(f"[MCP Tool] Response generated: {response_text[:100]}...")

                return {"answer": response_text}

        except asyncio.TimeoutError:
            logger.error("[MCP Tool] Request timeout")
            return {"answer": "Your question took too long to process. Please try again."}
        except Exception as e:
            logger.error(f"[MCP Tool] Unexpected error: {str(e)}")
            return {
                "answer": "I encountered an unexpected error. Please rephrase your question."
            }

    async def _parse_streaming_response(
        self, response: httpx.Response, client: httpx.AsyncClient, endpoint: str, query: str
    ) -> str:
        """
        Parse streaming response from backend.
        Falls back to regular POST if streaming fails.
        """
        try:
            # Try to parse as streaming response
            full_response = ""
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        event_data = json.loads(line[5:].strip())
                        if "content" in event_data:
                            full_response += event_data["content"]
                    except json.JSONDecodeError:
                        continue

            if full_response:
                return full_response

            # Fallback: try regular JSON response
            data = response.json()
            if "response" in data:
                return data["response"]
            if "answer" in data:
                return data["answer"]

            return "No response generated from the platform agent."

        except Exception as e:
            logger.warning(f"[MCP Tool] Streaming parse failed: {str(e)}, using fallback")
            # Final fallback: make a new POST request without streaming
            try:
                async with httpx.AsyncClient(timeout=RESPONSE_TIMEOUT) as new_client:
                    fallback_response = await new_client.post(
                        endpoint,
                        json={
                            "message": query,
                            "session_id": "mcp_platform_support_fallback",
                            "system_context": SYSTEM_PROMPT,
                        },
                    )
                    if fallback_response.status_code == 200:
                        data = fallback_response.json()
                        return data.get("response", data.get("answer", "No response"))
            except Exception as fallback_error:
                logger.error(f"[MCP Tool] Fallback also failed: {str(fallback_error)}")

            return "I couldn't generate a response. Please try rephrasing your question."


# Tool instance
query_tool = QueryPlatformSupportingTool()
