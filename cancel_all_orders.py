"""
Cancel all outstanding orders for an Orderly account
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/cancel-order
"""
import os
import sys
import argparse
import time
from dotenv import load_dotenv
from orderly_auth import create_authenticated_request, hex_to_private_key
import requests
from urllib.parse import urlencode
from privy_utils import get_account_id, get_wallet_address
from orderly_constants import ORDERLY_API_URL, BROKER_ID
from orderly_db import get_orderly_keys_or_raise
from get_orders import get_orders

load_dotenv()


def cancel_order(wallet_id: str, order_id: int, symbol: str) -> dict:
    """Cancel a single order on Orderly Network"""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    
    # Get Orderly keys from database
    orderly_key, orderly_private_key_hex = get_orderly_keys_or_raise(wallet_id)
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    account_id = get_account_id(wallet_address, BROKER_ID)
    
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
    
    return {
        "success": True,
        "data": data.get("data"),
        "status": data.get("data", {}).get("status"),
        "orderId": order_id,
        "symbol": symbol,
    }


def cancel_all_orders(wallet_id: str) -> dict:
    """
    Cancel all outstanding orders for an Orderly account
    
    Args:
        wallet_id: The Privy wallet ID (required)
        
    Returns:
        Summary of cancelled orders
    """
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    
    # Get wallet address
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\n📋 Fetching all orders...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    
    # Fetch all orders (handle pagination)
    all_orders = []
    page = 1
    page_size = 500  # Maximum page size
    
    while True:
        print(f"   Fetching page {page}...")
        result = get_orders(
            wallet_id=wallet_id,
            page=page,
            size=page_size
        )
        
        orders = result.get("orders", [])
        if not orders:
            break
        
        all_orders.extend(orders)
        
        # Check if there are more pages
        meta = result.get("meta", {})
        total = meta.get("total", len(orders))
        current_page = meta.get("current_page", page)
        records_per_page = meta.get("records_per_page", page_size)
        
        if len(all_orders) >= total:
            break
        
        page += 1
    
    print(f"\n✅ Found {len(all_orders)} total order(s)")
    
    # Filter cancellable orders (NEW and PARTIAL_FILLED)
    cancellable_statuses = ["NEW", "PARTIAL_FILLED"]
    
    cancellable_orders = [
        order for order in all_orders
        if order.get("status", "").upper() in cancellable_statuses
    ]
    
    if not cancellable_orders:
        print(f"\n✅ No cancellable orders found (status: {', '.join(cancellable_statuses)}).")
        return {
            "success": True,
            "cancelled_count": 0,
            "orders": [],
            "walletAddress": wallet_address,
            "accountId": account_id,
        }
    
    print(f"\n📈 Found {len(cancellable_orders)} cancellable order(s) to cancel:")
    print("-" * 100)
    
    for idx, order in enumerate(cancellable_orders, 1):
        order_id = order.get("order_id")
        symbol = order.get("symbol", "N/A")
        side = order.get("side", "N/A")
        order_type = order.get("type", "N/A")
        status = order.get("status", "N/A")
        quantity = order.get("quantity", 0)
        price = order.get("price", 0)
        
        print(f"{idx}. Order #{order_id}: {symbol} {side} {order_type} - Qty: {quantity} @ ${price} (Status: {status})")
    
    print("\n🔄 Cancelling all orders...")
    print("-" * 100)
    
    cancelled_orders = []
    failed_orders = []
    
    for idx, order in enumerate(cancellable_orders, 1):
        order_id = order.get("order_id")
        symbol = order.get("symbol", "N/A")
        side = order.get("side", "N/A")
        order_type = order.get("type", "N/A")
        quantity = order.get("quantity", 0)
        price = order.get("price", 0)
        
        print(f"\n[{idx}/{len(cancellable_orders)}] Cancelling Order #{order_id} ({symbol})...")
        
        try:
            cancel_result = cancel_order(wallet_id, order_id, symbol)
            
            print(f"   ✅ Order cancelled successfully: Status {cancel_result.get('status', 'N/A')}")
            
            cancelled_orders.append({
                "orderId": order_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "status": "success"
            })
            
            # Small delay between cancellations to avoid rate limiting
            if idx < len(cancellable_orders):
                time.sleep(0.3)
                
        except Exception as error:
            print(f"   ❌ Failed to cancel order: {error}")
            failed_orders.append({
                "orderId": order_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "error": str(error),
                "status": "failed"
            })
    
    print("\n" + "=" * 100)
    print("\n📝 Cancellation Summary:")
    print(f"   Total Cancellable Orders: {len(cancellable_orders)}")
    print(f"   Successfully Cancelled: {len(cancelled_orders)}")
    print(f"   Failed: {len(failed_orders)}")
    
    if cancelled_orders:
        print("\n✅ Successfully Cancelled Orders:")
        for order in cancelled_orders:
            print(f"   - Order #{order['orderId']}: {order['symbol']} {order['side']} {order['type']} "
                  f"(Qty: {order['quantity']} @ ${order['price']})")
    
    if failed_orders:
        print("\n❌ Failed to Cancel Orders:")
        for order in failed_orders:
            print(f"   - Order #{order['orderId']}: {order['symbol']} {order['side']} {order['type']} "
                  f"- Error: {order['error']}")
    
    return {
        "success": len(failed_orders) == 0,
        "cancelled_count": len(cancelled_orders),
        "failed_count": len(failed_orders),
        "cancelled_orders": cancelled_orders,
        "failed_orders": failed_orders,
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Cancel all outstanding orders for an Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    
    args = parser.parse_args()
    
    try:
        result = cancel_all_orders(
            wallet_id=args.wallet_id
        )
        
        if result["success"]:
            print("\n✅ All orders cancelled successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Cancelled {result['cancelled_count']} orders, but {result['failed_count']} failed.")
            sys.exit(1)
            
    except Exception as error:
        print(f"\n❌ Failed to cancel orders: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
