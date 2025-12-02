"""
Simple MCP Client to test the MCP server
Connects via HTTP and lists available tools using FastMCP
"""
import asyncio
import argparse
from fastmcp import Client


async def main(server_url: str):
    """Main function to test the MCP server connection"""
    print(f"Connecting to MCP server at {server_url}...")
    
    try:
        async with Client(server_url) as client:
            tools = await client.list_tools()
            
            print(f"\nFound {len(tools)} tool(s):\n")
            
            for tool in tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")
                print()
            
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        print("\nMake sure the MCP server is running:")
        print("  python mcp_server.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MCP Client to test MCP server and list available tools"
    )
    parser.add_argument(
        "--server",
        "-s",
        type=str,
        default="http://localhost:8000/mcp",
        help="MCP server URL (default: http://localhost:8000/mcp)"
    )
    
    args = parser.parse_args()
    asyncio.run(main(args.server))
