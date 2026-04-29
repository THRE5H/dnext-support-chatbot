"""
MCP Server Launcher
Starts the Model Context Protocol server for integration with Haotian's RAG system
Run with: python mcp_launcher.py
"""

import logging
import os
from pathlib import Path

from config import Config
from database import DatabaseRepository
from auth_service import AuthenticationService
from mcp_server import start_mcp_server

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


def main():
    """Initialize and start the MCP server"""
    print("=" * 60)
    print("🤖 MCP Server - Platform Supporting Agent")
    print("=" * 60)
    
    try:
        # Initialize database and auth
        logger.info("Initializing database connection...")
        db = DatabaseRepository("data/chatbot.db")
        auth = AuthenticationService(db)
        
        # Get MCP port from environment or use default
        mcp_port = int(os.getenv("MCP_PORT", "8000"))
        
        print("\n" + "=" * 60)
        print("✅ Components initialized:")
        print(f"  • Database: data/chatbot.db")
        print(f"  • Auth Service: Active")
        print(f"  • MCP Server Port: {mcp_port}")
        print("=" * 60)
        print("\n📋 Integration Instructions for Haotian:")
        print(f"  1. Register MCP server in agent config:")
        print(f"     url: http://<your-host>:{mcp_port}/mcp")
        print(f"  2. Tool available: query_platform_supporting")
        print(f"  3. Send POST requests with JSON-RPC 2.0 format")
        print("\n" + "=" * 60)
        
        # Start MCP server
        start_mcp_server(port=mcp_port, db=db, auth=auth)
    
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    main()
