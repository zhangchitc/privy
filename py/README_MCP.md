# MCP Server for Privy/Orderly Network

This MCP (Model Context Protocol) server exposes all Privy and Orderly Network operations as tools that can be used by AI assistants. Built with FastMCP for simplicity and ease of use.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file is configured with all required credentials:
- `PRIVY_APP_ID`
- `PRIVY_APP_SECRET`
- `PRIVY_AUTHORIZATION_ID`
- `PRIVY_AUTHORIZATION_SECRET`
- `ORDERLY_KEY` (after adding Orderly key)
- `ORDERLY_PRIVATE_KEY` (after adding Orderly key)

## Available Tools

The MCP server exposes the following tools:

### Wallet Management
- **create_agentic_wallet**: Creates an agentic wallet using Privy
- **register_orderly_account**: Registers an account on Orderly Network
- **add_orderly_key**: Adds an Orderly key for authenticated API calls

### Trading Operations
- **deposit_usdc**: Deposits USDC to an Orderly account
- **get_holding**: Gets current holdings from an Orderly account
- **create_order**: Creates a trading order on Orderly Network
- **get_orders**: Gets orders from an Orderly account with filtering
- **cancel_order**: Cancels an order on Orderly Network
- **withdraw_funds**: Withdraws funds from an Orderly account

### Transaction Operations
- **send_transaction**: Sends a transaction from an agentic wallet

## Usage

### Running the MCP Server

The server communicates via stdio (standard input/output) by default:

```bash
python mcp_server.py
```

For HTTP transport (web deployments):
```python
mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
```

### MCP Client Configuration

Add the server to your MCP client configuration. Example configuration:

```json
{
  "mcpServers": {
    "privy-orderly": {
      "command": "python",
      "args": ["/absolute/path/to/privy/py/mcp_server.py"],
      "cwd": "/absolute/path/to/privy/py"
    }
  }
}
```

### Using with Claude Desktop

1. Edit your Claude Desktop configuration file (location depends on OS):
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the MCP server configuration:

```json
{
  "mcpServers": {
    "privy-orderly": {
      "command": "python",
      "args": ["/absolute/path/to/privy/py/mcp_server.py"],
      "cwd": "/absolute/path/to/privy/py"
    }
  }
}
```

3. Restart Claude Desktop

### Example Tool Calls

Once connected, you can use the tools in conversations:

- "Create a new agentic wallet"
- "Register my wallet with Orderly Network"
- "Check my current holdings"
- "Create a LIMIT BUY order for PERP_ETH_USDC at price 2000 with quantity 0.1"
- "Get all my open orders"
- "Cancel order ID 12345"

## Tool Parameters

Each tool has detailed parameter descriptions in the tool schema. Required parameters are marked, and optional parameters have defaults where applicable.

## Error Handling

All tools return JSON responses. Errors are returned as text content with error messages for debugging.

## Notes

- Make sure your wallet is registered with Orderly before attempting trading operations
- Add an Orderly key before making authenticated API calls
- Ensure sufficient balance before depositing or trading
- Minimum withdrawal amount is 1.001

