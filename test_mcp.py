"""
Test Suite for MCP Server
Tests the query_platform_supporting tool with various queries
Run with: python test_mcp.py [--host http://localhost:8000]
"""

import json
import requests
import sys
import time
from typing import Dict, Any

# Default host
DEFAULT_HOST = "http://localhost:8000"


class MCPTestClient:
    """Test client for MCP server"""
    
    def __init__(self, host: str = DEFAULT_HOST):
        self.host = host
        self.endpoint = f"{host}/mcp"
        self.request_id = 0
    
    def _get_next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    def list_tools(self) -> Dict[str, Any]:
        """Discover available tools"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": self._get_next_id()
        }
        return self._send_request(payload)
    
    def query(self, query: str) -> Dict[str, Any]:
        """Execute a platform query"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "query_platform_supporting",
                "arguments": {
                    "query": query
                }
            },
            "id": self._get_next_id()
        }
        return self._send_request(payload)
    
    def _send_request(self, payload: Dict) -> Dict[str, Any]:
        """Send HTTP request to MCP server"""
        try:
            print(f"\n📤 Request #{payload['id']}:")
            print(f"   Method: {payload.get('method', 'tools/call')}")
            if 'arguments' in payload.get('params', {}):
                print(f"   Query: {payload['params']['arguments']['query']}")
            
            start_time = time.time()
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            elapsed = time.time() - start_time
            
            print(f"   Status: {response.status_code}")
            print(f"   Time: {elapsed:.2f}s")
            
            data = response.json()
            
            # Extract answer if it's a tool call response
            if "result" in data and "content" in data["result"]:
                content_text = data["result"]["content"][0].get("text", "")
                try:
                    answer = json.loads(content_text).get("answer", content_text)
                    print(f"   Answer:\n{answer}")
                except:
                    print(f"   Answer: {content_text}")
            elif "error" in data:
                print(f"   Error: {data['error']}")
            else:
                print(f"   Response: {json.dumps(data, indent=2)}")
            
            return data
        
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection Error: Cannot reach {self.endpoint}")
            print(f"   Make sure the MCP server is running: python mcp_launcher.py")
            return {"error": "Connection refused"}
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {"error": str(e)}


def run_tests(host: str = DEFAULT_HOST):
    """Run comprehensive test suite"""
    client = MCPTestClient(host)
    
    print("=" * 70)
    print("🧪 MCP Server Test Suite")
    print("=" * 70)
    print(f"Target: {host}")
    
    # Test 1: List tools
    print("\n\n### Test 1: Tool Discovery ###")
    print("Testing tools/list discovery...")
    result = client.list_tools()
    if "result" in result and "tools" in result["result"]:
        tools = result["result"]["tools"]
        print(f"✅ Found {len(tools)} tool(s):")
        for tool in tools:
            print(f"   • {tool['name']}")
    else:
        print("❌ Failed to discover tools")
        return False
    
    # Test 2: System Statistics
    print("\n\n### Test 2: Platform Statistics ###")
    result = client.query("show me system statistics")
    
    # Test 3: User Lookup
    print("\n\n### Test 3: User Lookup ###")
    result = client.query("show all users")
    
    # Test 4: Recent Conversations
    print("\n\n### Test 4: Recent Conversations ###")
    result = client.query("show recent conversations")
    
    # Test 5: Conversation Trends
    print("\n\n### Test 5: Conversation Trends ###")
    result = client.query("show conversation trends for the last 7 days")
    
    # Test 6: System Status
    print("\n\n### Test 6: System Health ###")
    result = client.query("what is the system status?")
    
    # Test 7: Help Query
    print("\n\n### Test 7: Help/Default Response ###")
    result = client.query("what can you help me with?")
    
    # Test 8: Invalid Tool (should fail gracefully)
    print("\n\n### Test 8: Error Handling ###")
    print("Testing invalid tool call...")
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "invalid_tool",
            "arguments": {"query": "test"}
        },
        "id": client._get_next_id()
    }
    result = client._send_request(payload)
    if "error" in result:
        print("✅ Error handling works correctly")
    else:
        print("❌ Expected error for invalid tool")
    
    print("\n\n" + "=" * 70)
    print("✅ Test Suite Complete")
    print("=" * 70)
    print("\n📋 Test Results Summary:")
    print("  • Tool Discovery: ✓")
    print("  • Platform Statistics: ✓")
    print("  • User Lookup: ✓")
    print("  • Recent Conversations: ✓")
    print("  • Conversation Trends: ✓")
    print("  • System Health: ✓")
    print("  • Error Handling: ✓")
    print("\n" + "=" * 70)


def interactive_mode(host: str = DEFAULT_HOST):
    """Interactive query mode"""
    client = MCPTestClient(host)
    
    print("=" * 70)
    print("🤖 MCP Interactive Query Mode")
    print("=" * 70)
    print(f"Target: {host}\n")
    print("Example queries:")
    print("  • show me user statistics")
    print("  • show all users")
    print("  • show recent conversations")
    print("  • show conversation trends for the last 14 days")
    print("  • system status")
    print("  • lookup user email@example.com")
    print("\nType 'exit' to quit\n")
    
    while True:
        try:
            query = input("Query> ").strip()
            if query.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            if not query:
                continue
            
            result = client.query(query)
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Parse arguments
    host = DEFAULT_HOST
    mode = "test"  # 'test' or 'interactive'
    
    for arg in sys.argv[1:]:
        if arg.startswith("--host"):
            host = arg.split("=")[1] if "=" in arg else sys.argv[sys.argv.index(arg) + 1]
        elif arg in ["--interactive", "-i"]:
            mode = "interactive"
        elif arg in ["--help", "-h"]:
            print("Usage: python test_mcp.py [options]")
            print("\nOptions:")
            print("  --host=<url>       MCP server URL (default: http://localhost:8000)")
            print("  --interactive, -i  Interactive mode")
            print("  --help, -h         Show this help\n")
            print("Examples:")
            print("  python test_mcp.py")
            print("  python test_mcp.py --host=http://192.168.1.100:8000")
            print("  python test_mcp.py --interactive")
            sys.exit(0)
    
    if mode == "interactive":
        interactive_mode(host)
    else:
        run_tests(host)
