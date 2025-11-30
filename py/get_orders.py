"""
Get orders from Orderly account
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-orders
"""
import os
import sys
import argparse
import base64
from dotenv import load_dotenv
from web3 import Web3
from eth_abi import encode
from eth_utils import keccak, to_hex
from orderly_auth import create_authenticated_request, hex_to_private_key
import requests
from urllib.parse import urlencode

load_dotenv()

# Configuration
ORDERLY_API_URL = "https://api.orderly.org"
BROKER_ID = "woofi_pro"

PRIVY_API_BASE = "https://auth.privy.io/api/v1"


def get_account_id(address: str, broker_id: str) -> str:
    """Generate Orderly account ID"""
    broker_id_hash = keccak(broker_id.encode())
    encoded = encode(["address", "bytes32"], [address, broker_id_hash])
    return to_hex(keccak(encoded))


def get_wallet_address(wallet_id: str, app_id: str, app_secret: str) -> str:
    """Get wallet address from Privy"""
    auth_string = f"{app_id}:{app_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "privy-app-id": app_id,
        "Content-Type": "application/json"
    }
    response = requests.get(f"{PRIVY_API_BASE}/wallets/{wallet_id}", headers=headers)
    if not response.ok:
        raise Exception(f"Failed to get wallet: {response.text}")
    wallet = response.json()
    wallet_address = (
        wallet.get("address") or
        (wallet.get("addresses", [{}])[0].get("address") if wallet.get("addresses") else None) or
        (wallet.get("addresses", [None])[0] if wallet.get("addresses") else None)
    )
    if not wallet_address:
        raise Exception("Could not determine wallet address from wallet object")
    return wallet_address


def get_orders(
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
    sort_by: str = None,
) -> dict:
    """Get orders from Orderly account"""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    orderly_key = os.getenv("ORDERLY_KEY")
    orderly_private_key_hex = os.getenv("ORDERLY_PRIVATE_KEY")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    if not orderly_key:
        raise ValueError("ORDERLY_KEY environment variable is required")
    if not orderly_private_key_hex:
        raise ValueError("ORDERLY_PRIVATE_KEY environment variable is required")
    
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    if not wallet_address:
        print("Fetching wallet details...")
        wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
        print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nFetching orders from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    
    # Build query parameters
    query_params = {}
    if symbol:
        query_params["symbol"] = symbol
    if side:
        query_params["side"] = side.upper()
    if order_type:
        query_params["order_type"] = order_type.upper()
    if status:
        query_params["status"] = status.upper()
    if order_tag:
        query_params["order_tag"] = order_tag
    if start_time:
        query_params["start_t"] = str(start_time)
    if end_time:
        query_params["end_t"] = str(end_time)
    if page:
        query_params["page"] = str(page)
    if size:
        query_params["size"] = str(size)
    if sort_by:
        query_params["sort_by"] = sort_by
    
    query_string = urlencode(query_params)
    path = f"/v1/orders?{query_string}" if query_string else "/v1/orders"
    
    if query_string:
        print(f"   Filters: {query_string}")
    
    # Create authenticated request
    request_config = create_authenticated_request(
        "GET",
        path,
        None,
        account_id,
        orderly_key,
        orderly_private_key
    )
    
    # Make the request
    response = requests.get(
        f"{ORDERLY_API_URL}{path}",
        headers=request_config["headers"]
    )
    
    data = response.json()
    
    if not response.ok:
        raise Exception(f"Failed to get orders: {data}")
    
    if not data.get("success"):
        raise Exception(f"Orderly API returned error: {data}")
    
    print("\n✅ Orders retrieved successfully!")
    
    return {
        "success": True,
        "data": data.get("data"),
        "orders": data.get("data", {}).get("rows", []),
        "meta": data.get("data", {}).get("meta", {}),
        "timestamp": data.get("timestamp"),
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Get orders from Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--wallet-address", help="Wallet address (optional, will be fetched if not provided)")
    parser.add_argument("--symbol", help="Trading symbol filter (e.g., 'PERP_ETH_USDC')")
    parser.add_argument("--side", choices=["BUY", "SELL"], help="Order side filter: BUY or SELL")
    parser.add_argument("--order-type", choices=["LIMIT", "MARKET"], help="Order type filter: LIMIT or MARKET")
    parser.add_argument("--status", help="Order status filter: NEW, CANCELLED, PARTIAL_FILLED, FILLED, REJECTED, INCOMPLETE, COMPLETED")
    parser.add_argument("--order-tag", help="Order tag filter")
    parser.add_argument("--start-time", type=int, help="Start time range (13-digit timestamp in milliseconds)")
    parser.add_argument("--end-time", type=int, help="End time range (13-digit timestamp in milliseconds)")
    parser.add_argument("--page", type=int, default=1, help="Page number (starts from 1, default: 1)")
    parser.add_argument("--size", type=int, default=25, help="Page size (max: 500, default: 25)")
    parser.add_argument("--sort-by", help="Sort by: CREATED_TIME_DESC, CREATED_TIME_ASC, UPDATED_TIME_DESC, UPDATED_TIME_ASC")
    
    args = parser.parse_args()
    
    try:
        result = get_orders(
            wallet_id=args.wallet_id,
            wallet_address=args.wallet_address,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            status=args.status,
            order_tag=args.order_tag,
            start_time=args.start_time,
            end_time=args.end_time,
            page=args.page,
            size=args.size,
            sort_by=args.sort_by,
        )
        
        # Display orders
        print("\n📋 Orders:")
        print("=" * 100)
        
        if not result["orders"]:
            print("   No orders found.")
        else:
            if result["meta"].get("total") is not None:
                print(f"\nTotal Orders: {result['meta']['total']}")
                total_pages = (result["meta"].get("total", 0) + result["meta"].get("records_per_page", 25) - 1) // result["meta"].get("records_per_page", 25)
                print(f"Page: {result['meta'].get('current_page', 1)} of {total_pages}")
                print(f"Records per page: {result['meta'].get('records_per_page', 25)}")
            
            for index, order in enumerate(result["orders"], 1):
                print(f"\n{index}. Order #{order.get('order_id')}:")
                print(f"   Symbol: {order.get('symbol')}")
                print(f"   Side: {order.get('side')}")
                print(f"   Type: {order.get('type')}")
                print(f"   Status: {order.get('status')}")
                print(f"   Price: {order.get('price')}")
                print(f"   Quantity: {order.get('quantity')}")
                if order.get("amount") is not None:
                    print(f"   Amount: {order.get('amount')}")
                print(f"   Executed Quantity: {order.get('executed_quantity')}")
                print(f"   Total Executed Quantity: {order.get('total_executed_quantity')}")
                print(f"   Visible Quantity: {order.get('visible_quantity')}")
                print(f"   Average Executed Price: {order.get('average_executed_price')}")
                print(f"   Total Fee: {order.get('total_fee')} {order.get('fee_asset')}")
                if order.get("client_order_id") is not None:
                    print(f"   Client Order ID: {order.get('client_order_id')}")
                print(f"   Realized PnL: {order.get('realized_pnl')}")
                print(f"   Created: {order.get('created_time')}")
                print(f"   Updated: {order.get('updated_time')}")
        
        print("\n" + "=" * 100)
        print("\n📝 Summary:")
        print(f"   Wallet Address: {result['walletAddress']}")
        print(f"   Account ID: {result['accountId']}")
        print(f"   Number of Orders: {len(result['orders'])}")
        if result["meta"].get("total") is not None:
            print(f"   Total Orders: {result['meta']['total']}")
        print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to get orders: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

