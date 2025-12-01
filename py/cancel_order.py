"""
Cancel an order on Orderly Network using Privy agentic wallet
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/cancel-order
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from web3 import Web3
from orderly_auth import create_authenticated_request, hex_to_private_key
import requests
from urllib.parse import urlencode
from privy_utils import get_account_id, get_wallet_address
from orderly_constants import ORDERLY_API_URL, BROKER_ID

load_dotenv()


def cancel_order(wallet_id: str, order_id: int = None, symbol: str = None) -> dict:
    """Cancel an order on Orderly Network"""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    orderly_key = os.getenv("ORDERLY_KEY")
    orderly_private_key_hex = os.getenv("ORDERLY_PRIVATE_KEY")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    if not order_id:
        raise ValueError("Order ID is required")
    if not symbol:
        raise ValueError("Symbol is required")
    if not orderly_key:
        raise ValueError("ORDERLY_KEY environment variable is required")
    if not orderly_private_key_hex:
        raise ValueError("ORDERLY_PRIVATE_KEY environment variable is required")
    
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nPreparing order cancellation...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    print(f"   Order ID: {order_id}")
    print(f"   Symbol: {symbol}")
    
    # Build query parameters
    query_params = urlencode({
        "order_id": str(order_id),
        "symbol": symbol
    })
    path = f"/v1/order?{query_params}"
    
    # Create authenticated request
    request_config = create_authenticated_request(
        "DELETE",
        path,
        None,
        account_id,
        orderly_key,
        orderly_private_key
    )
    
    # Make the request
    response = requests.delete(
        f"{ORDERLY_API_URL}{path}",
        headers=request_config["headers"]
    )
    
    data = response.json()
    
    if not response.ok:
        raise Exception(f"Failed to cancel order: {data}")
    
    if not data.get("success"):
        raise Exception(f"Cancel order failed: {data}")
    
    print("\n✅ Order cancelled successfully!")
    print(f"Response: {data}")
    
    return {
        "success": True,
        "data": data.get("data"),
        "status": data.get("data", {}).get("status"),
        "orderId": order_id,
        "symbol": symbol,
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Cancel an order on Orderly Network")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--order-id", type=int, required=True, help="Order ID to cancel (required)")
    parser.add_argument("--symbol", required=True, help="Trading symbol (e.g., 'PERP_ETH_USDC') (required)")
    
    args = parser.parse_args()
    
    try:
        result = cancel_order(
            wallet_id=args.wallet_id,
            order_id=args.order_id,
            symbol=args.symbol
        )
        
        print("\n📝 Cancellation Summary:")
        print(f"   Wallet Address: {result['walletAddress']}")
        print(f"   Account ID: {result['accountId']}")
        print(f"   Order ID: {result['orderId']}")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Status: {result.get('status', 'N/A')}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to cancel order: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

