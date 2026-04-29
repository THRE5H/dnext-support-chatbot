"""
MCP Server for Platform Supporting Agent
Exposes a query_platform_supporting tool to Haotian's RAG system
Protocol: MCP (Model Context Protocol) version >= 2025-06-18
"""

import json
import logging
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading

from config import Config
from database import DatabaseRepository
from auth_service import AuthenticationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] MCP_SERVER - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


class PlatformSupportingAgent:
    """
    Dhia's supporting agent that answers platform/support questions
    Handles queries about system usage, user data, and conversation history
    """
    
    def __init__(self, db: DatabaseRepository, auth: AuthenticationService):
        self.db = db
        self.auth = auth
    
    def query(self, question: str) -> str:
        """
        Process natural language query and return answer
        Supports: user lookup, conversation history, statistics, analytics
        """
        try:
            question_lower = question.lower().strip()
            
            # ─────────────────────────────────────────────────────
            # User Statistics & Analytics
            # ─────────────────────────────────────────────────────
            if any(word in question_lower for word in ["statistics", "stats", "overview", "summary", "total"]):
                stats = self.db.get_statistics()
                return self._format_statistics(stats)
            
            # ─────────────────────────────────────────────────────
            # User Lookup Queries
            # ─────────────────────────────────────────────────────
            if "user" in question_lower and "email" in question_lower:
                # Extract email if provided
                email = self._extract_email(question)
                if email:
                    user = self.db.get_user_by_email(email)
                    if user:
                        return self._format_user_info(user)
                    else:
                        return f"User with email '{email}' not found in the system."
                return "Please provide an email address to look up a user."
            
            if "all users" in question_lower or "user list" in question_lower:
                users = self.db.get_all_users(limit=10)
                if users:
                    return self._format_user_list(users)
                return "No users found in the system."
            
            # ─────────────────────────────────────────────────────
            # Conversation History & Session Data
            # ─────────────────────────────────────────────────────
            if "recent conversation" in question_lower or "recent messages" in question_lower:
                conversations = self.db.get_recent_conversations(limit=10)
                if conversations:
                    return self._format_recent_conversations(conversations)
                return "No recent conversations found."
            
            if "conversation" in question_lower and ("session" in question_lower or "history" in question_lower):
                # User would need to provide user_id context
                return "To retrieve conversation history, please specify a user ID or email address."
            
            # ─────────────────────────────────────────────────────
            # Time-based Analytics
            # ─────────────────────────────────────────────────────
            if "trend" in question_lower or "timeseries" in question_lower or "last" in question_lower and "days" in question_lower:
                days = self._extract_days(question)
                timeseries = self.db.get_conversations_timeseries(days=days)
                if timeseries:
                    return self._format_timeseries(timeseries, days)
                return f"No conversation data available for the past {days} days."
            
            # ─────────────────────────────────────────────────────
            # System Health & Status
            # ─────────────────────────────────────────────────────
            if any(word in question_lower for word in ["health", "status", "active", "system"]):
                return self._get_system_status()
            
            # ─────────────────────────────────────────────────────
            # Default: Clarification Request
            # ─────────────────────────────────────────────────────
            return (
                "I'm Dhia's Platform Supporting Agent. I can help you with:\n"
                "• User statistics and analytics\n"
                "• User lookups (by email)\n"
                "• Recent conversations and chat history\n"
                "• Conversation trends and timeseries data\n"
                "• System health and status\n\n"
                "Please ask a specific question about the platform data, e.g., "
                "'show me user statistics' or 'lookup user email@example.com'"
            )
        
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"Error processing your query: {str(e)}"
    
    # ───────────────────────────────────────────────────────────────
    # Formatting Methods
    # ───────────────────────────────────────────────────────────────
    
    def _format_statistics(self, stats: dict) -> str:
        """Format system statistics for display"""
        lines = [
            "📊 Platform Statistics:",
            f"  • Total Users: {stats.get('total_users', 0)}",
            f"  • Total Conversations: {stats.get('total_conversations', 0)}",
            f"  • Active Users (last 7 days): {stats.get('active_users_7d', 0)}",
            f"  • Average Response Time: {stats.get('avg_response_time_ms', 0):.0f}ms",
        ]
        return "\n".join(lines)
    
    def _format_user_info(self, user) -> str:
        """Format individual user information"""
        lines = [
            f"👤 User Information:",
            f"  • Name: {user.full_name}",
            f"  • Email: {user.email}",
            f"  • Status: {user.status}",
            f"  • Total Queries: {user.total_queries}",
            f"  • Created: {user.created_at}",
        ]
        if user.last_login:
            lines.append(f"  • Last Login: {user.last_login}")
        return "\n".join(lines)
    
    def _format_user_list(self, users: list) -> str:
        """Format list of users"""
        lines = ["👥 Recent Users:"]
        for i, user in enumerate(users[:10], 1):
            lines.append(f"  {i}. {user.full_name} ({user.email}) - Status: {user.status}")
        return "\n".join(lines)
    
    def _format_recent_conversations(self, conversations: list) -> str:
        """Format recent conversations"""
        lines = ["💬 Recent Conversations:"]
        for i, (conv, user) in enumerate(conversations[:5], 1):
            preview = conv.message[:50] + "..." if len(conv.message) > 50 else conv.message
            lines.append(f"  {i}. {user.full_name}: {preview}")
            lines.append(f"     Response time: {conv.response_time_ms}ms | {conv.timestamp}")
        return "\n".join(lines)
    
    def _format_timeseries(self, timeseries: list, days: int) -> str:
        """Format timeseries conversation data"""
        lines = [f"📈 Conversation Trend (Last {days} days):"]
        total = 0
        for date, count in timeseries:
            lines.append(f"  {date}: {count} conversations")
            total += count
        lines.append(f"  Total: {total} conversations")
        return "\n".join(lines)
    
    def _get_system_status(self) -> str:
        """Get system health status"""
        try:
            stats = self.db.get_statistics()
            return (
                f"✅ System Status: Operational\n"
                f"  • Database: Connected\n"
                f"  • Active Users: {stats.get('active_users_7d', 0)}\n"
                f"  • Total Conversations: {stats.get('total_conversations', 0)}\n"
                f"  • Last Updated: Now"
            )
        except Exception as e:
            return f"⚠️ System Status: Warning\nDatabase connection issue: {str(e)}"
    
    # ───────────────────────────────────────────────────────────────
    # Helper Methods for Query Parsing
    # ───────────────────────────────────────────────────────────────
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from query text"""
        import re
        match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        return match.group(0) if match else None
    
    def _extract_days(self, text: str) -> int:
        """Extract number of days from query"""
        import re
        match = re.search(r'(\d+)\s*days?', text.lower())
        return int(match.group(1)) if match else 14


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP protocol"""
    
    # Share agent instance across requests
    agent = None
    
    def do_POST(self):
        """Handle POST requests to /mcp endpoint"""
        # Route to MCP handler
        if self.path == "/mcp":
            self.handle_mcp_request()
        else:
            self.send_error(404, "Not Found. Use POST /mcp")
    
    def handle_mcp_request(self):
        """Process MCP protocol request"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            logger.info(f"MCP Request received: {body[:200]}")
            
            # Parse JSON-RPC request
            request_data = json.loads(body)
            
            # Respond based on request type
            if request_data.get("method") == "tools/list":
                response = self._handle_tools_list()
            elif request_data.get("method") == "tools/call":
                response = self._handle_tools_call(request_data)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id"),
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
            logger.info(f"MCP Response sent successfully")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in MCP request: {e}")
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}", exc_info=True)
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def _handle_tools_list(self) -> dict:
        """MCP tools/list method - return available tools"""
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "query_platform_supporting",
                        "description": (
                            "Query Dhia's platform database to retrieve system information, user data, and conversation history. "
                            "This agent answers questions about: (1) User statistics and demographics, (2) Individual user lookups by email, "
                            "(3) Conversation history and chat records, (4) Conversation trends and timeseries analytics, (5) System health and status. "
                            "Does NOT answer: technical troubleshooting, AI model decisions, or product-specific feature questions—use your primary data catalog for those. "
                            "Use this tool when Haotian's planner needs to verify system metrics, audit user records, or analyze conversation patterns."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language question about platform data, users, or conversations"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
    
    def _handle_tools_call(self, request_data: dict) -> dict:
        """MCP tools/call method - execute the query_platform_supporting tool"""
        try:
            tool_name = request_data.get("params", {}).get("name")
            tool_input = request_data.get("params", {}).get("arguments", {})
            
            if tool_name != "query_platform_supporting":
                return {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id"),
                    "error": {
                        "code": -32602,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            # Execute the agent query
            query = tool_input.get("query", "")
            logger.info(f"Executing query_platform_supporting: {query[:100]}")
            
            answer = self.agent.query(query)
            
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"answer": answer})
                        }
                    ]
                }
            }
        
        except Exception as e:
            logger.error(f"Error executing tool: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def log_message(self, format, *args):
        """Override to use custom logger"""
        logger.info(format % args)


def start_mcp_server(port: int = 8000, db: Optional[DatabaseRepository] = None, auth: Optional[AuthenticationService] = None):
    """
    Start the MCP server
    
    Args:
        port: Port to listen on (default 8000)
        db: Database repository instance
        auth: Authentication service instance
    """
    if db is None or auth is None:
        logger.warning("Database or Auth not provided, initializing...")
        db = DatabaseRepository("data/chatbot.db")
        auth = AuthenticationService(db)
    
    # Initialize agent and attach to handler
    MCPRequestHandler.agent = PlatformSupportingAgent(db, auth)
    
    # Create and start server
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, MCPRequestHandler)
    
    logger.info("=" * 60)
    logger.info(f"🚀 MCP Server starting on http://0.0.0.0:{port}/mcp")
    logger.info("=" * 60)
    logger.info("Endpoint: POST http://0.0.0.0:{port}/mcp")
    logger.info("Tool: query_platform_supporting")
    logger.info("Protocol: MCP (Model Context Protocol) 2025-06-18+")
    logger.info("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n⏹️  MCP Server shutdown requested")
        httpd.shutdown()


if __name__ == "__main__":
    # Run standalone MCP server on port 8000
    start_mcp_server(port=8000)
