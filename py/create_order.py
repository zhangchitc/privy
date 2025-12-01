"""
Create an order on Orderly Network using Privy agentic wallet
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/create-order
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from web3 import Web3
from orderly_auth import create_authenticated_request, hex_to_private_key
import requests
from privy_utils import get_account_id, get_wallet_address
from orderly_constants import ORDERLY_API_URL, BROKER_ID

load_dotenv()


def create_order(
    wallet_id: str,
    symbol: str = None,
    order_type: str = None,
    side: str = None,
    order_price: float = None,
    order_quantity: float = None,
    order_amount: float = None,
    visible_quantity: float = None,
    reduce_only: bool = False,
    slippage: float = None,
    client_order_id: str = None,
    order_tag: str = None,
    level: int = None,
) -> dict:
    """Create an order on Orderly Network"""
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
    
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    # Validate required fields
    if not symbol or not order_type or not side:
        raise ValueError("Missing required fields: symbol, orderType, and side are required")
    
    # Validate order type
    valid_order_types = ["LIMIT", "MARKET", "IOC", "FOK", "POST_ONLY", "ASK", "BID"]
    if order_type.upper() not in valid_order_types:
        raise ValueError(f"Invalid order type: {order_type}. Must be one of: {', '.join(valid_order_types)}")
    
    # Validate side
    if side.upper() not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side: {side}. Must be BUY or SELL")
    
    # Validate order_price requirement
    order_type_upper = order_type.upper()
    if order_type_upper in ["LIMIT", "IOC", "FOK", "POST_ONLY"] and order_price is None:
        raise ValueError(f"orderPrice is required for {order_type} orders")
    
    # Validate order_quantity or order_amount
    if order_quantity is None and order_amount is None:
        raise ValueError("Either orderQuantity or orderAmount must be provided")
    
    # Validate MARKET/BID/ASK order requirements
    if order_type_upper in ["MARKET", "BID", "ASK"]:
        if side.upper() == "SELL" and order_amount is not None:
            raise ValueError("orderAmount is not supported for SELL orders with MARKET/BID/ASK order types")
        if side.upper() == "BUY" and order_quantity is not None:
            raise ValueError("orderQuantity is not supported for BUY orders with MARKET/BID/ASK order types")
    
    print("\nPreparing order creation...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    print(f"   Symbol: {symbol}")
    print(f"   Order Type: {order_type}")
    print(f"   Side: {side}")
    
    # Build request body
    request_body = {
        "symbol": symbol,
        "order_type": order_type.upper(),
        "side": side.upper(),
    }
    
    if order_price is not None:
        request_body["order_price"] = order_price
    if order_quantity is not None:
        request_body["order_quantity"] = order_quantity
    if order_amount is not None:
        request_body["order_amount"] = order_amount
    if visible_quantity is not None:
        request_body["visible_quantity"] = visible_quantity
    if reduce_only is not None:
        request_body["reduce_only"] = reduce_only
    if slippage is not None:
        request_body["slippage"] = slippage
    if client_order_id is not None:
        request_body["client_order_id"] = client_order_id
    if order_tag is not None:
        request_body["order_tag"] = order_tag
    if level is not None:
        request_body["level"] = level
    
    print(f"\nOrder parameters: {request_body}")
    
    path = "/v1/order"
    request_config = create_authenticated_request(
        "POST",
        path,
        request_body,
        account_id,
        orderly_key,
        orderly_private_key
    )
    
    response = requests.post(
        f"{ORDERLY_API_URL}{path}",
        headers=request_config["headers"],
        data=request_config["body"]
    )
    
    data = response.json()
    
    if not response.ok:
        raise Exception(f"Failed to create order: {data}")
    
    if not data.get("success"):
        raise Exception(f"Order creation failed: {data}")
    
    print("\n✅ Order created successfully!")
    print(f"Response: {data}")
    
    return {
        "success": True,
        "data": data.get("data"),
        "orderId": data.get("data", {}).get("order_id"),
        "clientOrderId": data.get("data", {}).get("client_order_id"),
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Create an order on Orderly Network")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--symbol", required=True, help="Trading symbol (e.g., 'PERP_ETH_USDC') (required)")
    parser.add_argument("--order-type", required=True, help="Order type: LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID (required)")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side: BUY or SELL (required)")
    parser.add_argument("--order-price", type=float, help="Order price (required for LIMIT/IOC/FOK/POST_ONLY)")
    parser.add_argument("--order-quantity", type=float, help="Order quantity in base currency")
    parser.add_argument("--order-amount", type=float, help="Order amount in quote currency (for MARKET/BID/ASK BUY orders)")
    parser.add_argument("--visible-quantity", type=float, help="Visible quantity on orderbook")
    parser.add_argument("--reduce-only", action="store_true", help="Reduce only flag")
    parser.add_argument("--slippage", type=float, help="Slippage tolerance for MARKET orders")
    parser.add_argument("--client-order-id", help="Custom client order ID (36 chars max, unique)")
    parser.add_argument("--order-tag", help="Order tag")
    parser.add_argument("--level", type=int, help="Level for BID/ASK orders (0-4)")
    
    args = parser.parse_args()
    
    try:
        result = create_order(
            wallet_id=args.wallet_id,
            symbol=args.symbol,
            order_type=args.order_type,
            side=args.side,
            order_price=args.order_price,
            order_quantity=args.order_quantity,
            order_amount=args.order_amount,
            visible_quantity=args.visible_quantity,
            reduce_only=args.reduce_only,
            slippage=args.slippage,
            client_order_id=args.client_order_id,
            order_tag=args.order_tag,
            level=args.level,
        )
        
        print("\n📝 Order Summary:")
        print(f"   Wallet Address: {result['walletAddress']}")
        print(f"   Account ID: {result['accountId']}")
        print(f"   Order ID: {result['orderId']}")
        if result.get("clientOrderId"):
            print(f"   Client Order ID: {result['clientOrderId']}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to create order: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

