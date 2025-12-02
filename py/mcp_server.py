"""
MCP Server for Privy/Orderly Network operations
Exposes all Python scripts as MCP tools for AI assistants
Built with FastMCP for simplicity
"""
from fastmcp import FastMCP
from dotenv import load_dotenv

# Import all the script functions
from create_agentic_wallet import create_agentic_wallet
from register_orderly_account import register_orderly_account
from add_orderly_key import add_orderly_key
from deposit_usdc import deposit_usdc
from get_holding import get_holding
from create_order import create_order
from get_orders import get_orders
from cancel_order import cancel_order
from withdraw_usdc import withdraw_funds
from send_transaction import send_transaction

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Privy Orderly MCP Server")


@mcp.tool()
def create_agentic_wallet_tool(
    policy_id: str = None,
    chain_type: str = "ethereum"
) -> dict:
    """
    Creates an agentic wallet using Privy.
    
    Args:
        policy_id: Optional policy ID to assign to the wallet
        chain_type: Chain type ('ethereum' or 'solana'), defaults to 'ethereum'
    
    Returns:
        The created wallet object with ID and address
    """
    return create_agentic_wallet(policy_id=policy_id, chain_type=chain_type)


@mcp.tool()
def register_orderly_account_tool(
    wallet_id: str,
    wallet_address: str = None,
    chain_id: str = "421614"
) -> dict:
    """
    Registers an account on Orderly Network using a Privy agentic wallet.
    Required before trading operations.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        chain_id: Chain ID (optional, default: 421614 = Arbitrum Sepolia)
    
    Returns:
        Registration result with Orderly account ID
    """
    return register_orderly_account(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        chain_id=chain_id
    )


@mcp.tool()
def add_orderly_key_tool(
    wallet_id: str,
    wallet_address: str = None,
    chain_id: int = None
) -> dict:
    """
    Adds an Orderly key for a Privy wallet.
    Required for authenticated API calls to Orderly Network.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        chain_id: Chain ID (optional, default: 80001 = Polygon Mumbai)
    
    Returns:
        Result with generated Orderly key (saved to .env file)
    """
    return add_orderly_key(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        chain_id=chain_id
    )


@mcp.tool()
def deposit_usdc_tool(
    wallet_id: str,
    amount: str,
    wallet_address: str = None,
    chain_id: int = None
) -> dict:
    """
    Deposits USDC to an Orderly account.
    Requires wallet to be registered and have sufficient USDC balance.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        amount: Amount of USDC to deposit (required, e.g., '100')
        wallet_address: The wallet address (optional, will be fetched if not provided)
        chain_id: Chain ID (optional, default: 80001 = Polygon Mumbai)
    
    Returns:
        Deposit result with transaction hash and details
    """
    return deposit_usdc(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        amount=amount,
        chain_id=chain_id
    )


@mcp.tool()
def get_holding_tool(
    wallet_id: str,
    wallet_address: str = None,
    all: bool = False
) -> dict:
    """
    Gets current holdings from an Orderly account.
    Shows all tokens and their balances (total, frozen, available).
    
    Args:
        wallet_id: The Privy wallet ID (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        all: Include all tokens even if balance is empty (default: False)
    
    Returns:
        Holdings data with list of tokens and balances
    """
    return get_holding(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        all=all
    )


@mcp.tool()
def create_order_tool(
    wallet_id: str,
    symbol: str,
    order_type: str,
    side: str,
    wallet_address: str = None,
    order_price: float = None,
    order_quantity: float = None,
    order_amount: float = None,
    visible_quantity: float = None,
    reduce_only: bool = False,
    slippage: float = None,
    client_order_id: str = None,
    order_tag: str = None,
    level: int = None
) -> dict:
    """
    Creates a trading order on Orderly Network.
    Supports LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID order types.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        symbol: Trading symbol (e.g., 'PERP_ETH_USDC') (required)
        order_type: Order type: LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID (required)
        side: Order side: BUY or SELL (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        order_price: Order price (required for LIMIT/IOC/FOK/POST_ONLY)
        order_quantity: Order quantity in base currency
        order_amount: Order amount in quote currency (for MARKET/BID/ASK BUY orders)
        visible_quantity: Visible quantity on orderbook
        reduce_only: Reduce only flag (default: False)
        slippage: Slippage tolerance for MARKET orders
        client_order_id: Custom client order ID (36 chars max, unique)
        order_tag: Order tag
        level: Level for BID/ASK orders (0-4)
    
    Returns:
        Order creation result with order ID
    """
    return create_order(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        symbol=symbol,
        order_type=order_type,
        side=side,
        order_price=order_price,
        order_quantity=order_quantity,
        order_amount=order_amount,
        visible_quantity=visible_quantity,
        reduce_only=reduce_only,
        slippage=slippage,
        client_order_id=client_order_id,
        order_tag=order_tag,
        level=level
    )


@mcp.tool()
def get_orders_tool(
    wallet_id: str,
    wallet_address: str = None,
    symbol: str = None,
    side: str = None,
    order_type: str = None,
    status: str = None,
    order_tag: str = None,
    start_time: int = None,
    end_time: int = None,
    page: int = 1,
    size: int = 25,
    sort_by: str = None
) -> dict:
    """
    Gets orders from an Orderly account with filtering and pagination.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        symbol: Trading symbol filter (e.g., 'PERP_ETH_USDC')
        side: Order side filter: BUY or SELL
        order_type: Order type filter: LIMIT or MARKET
        status: Order status filter: NEW, CANCELLED, PARTIAL_FILLED, FILLED, REJECTED, INCOMPLETE, COMPLETED
        order_tag: Order tag filter
        start_time: Start time range (13-digit timestamp in milliseconds)
        end_time: End time range (13-digit timestamp in milliseconds)
        page: Page number (starts from 1, default: 1)
        size: Page size (max: 500, default: 25)
        sort_by: Sort by: CREATED_TIME_DESC, CREATED_TIME_ASC, UPDATED_TIME_DESC, UPDATED_TIME_ASC
    
    Returns:
        Orders data with list of orders and pagination info
    """
    return get_orders(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        symbol=symbol,
        side=side,
        order_type=order_type,
        status=status,
        order_tag=order_tag,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
        sort_by=sort_by
    )


@mcp.tool()
def cancel_order_tool(
    wallet_id: str,
    order_id: int,
    symbol: str,
    wallet_address: str = None
) -> dict:
    """
    Cancels an order on Orderly Network.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        order_id: Order ID to cancel (required)
        symbol: Trading symbol (e.g., 'PERP_ETH_USDC') (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
    
    Returns:
        Cancellation result with order status
    """
    return cancel_order(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        order_id=order_id,
        symbol=symbol
    )


@mcp.tool()
def withdraw_funds_tool(
    wallet_id: str,
    amount: str,
    wallet_address: str = None,
    token: str = "USDC",
    chain_id: int = None
) -> dict:
    """
    Withdraws funds from an Orderly account.
    Minimum withdrawal amount is 1.001.
    
    Args:
        wallet_id: The Privy wallet ID (required)
        amount: Amount to withdraw (required, e.g., '100')
        wallet_address: The wallet address (optional, will be fetched if not provided)
        token: Token symbol to withdraw (default: 'USDC')
        chain_id: Chain ID (optional, default: 80001 = Polygon Mumbai)
    
    Returns:
        Withdrawal result with withdrawal nonce and details
    """
    return withdraw_funds(
        wallet_id=wallet_id,
        wallet_address=wallet_address,
        amount=amount,
        token=token,
        chain_id=chain_id
    )


@mcp.tool()
def send_transaction_tool(
    wallet_id: str,
    to: str,
    value: str = "1000000000000000",
    chain_id: str = "11155111"
) -> dict:
    """
    Sends a transaction from an agentic wallet using Privy.
    
    Args:
        wallet_id: Wallet ID to send from (required)
        to: Recipient Ethereum address (required)
        value: Amount in wei (default: 1000000000000000 = 0.001 ETH)
        chain_id: Chain ID (default: 11155111 = Sepolia testnet)
    
    Returns:
        Transaction result with transaction hash
    """
    return send_transaction(
        wallet_id=wallet_id,
        to=to,
        value=value,
        chain_id=chain_id
    )


if __name__ == "__main__":
    # Run the MCP server using streamable HTTP transport (SSE)
    mcp.run(transport="http", host="localhost", port=8000, path="/mcp")
