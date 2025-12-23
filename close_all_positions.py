"""
Close all open positions for an Orderly account using MARKET orders
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/create-order
"""
import os
import sys
import argparse
import time
from dotenv import load_dotenv
from privy_utils import get_account_id, get_wallet_address
from orderly_constants import BROKER_ID
from get_positions import get_positions
from create_order import create_order

load_dotenv()


def close_all_positions(wallet_id: str) -> dict:
    """
    Close all open positions for an Orderly account using MARKET orders
    
    Args:
        wallet_id: The Privy wallet ID (required)
        
    Returns:
        Summary of closed positions
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
    
    print("\n📊 Fetching current positions...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    
    # Get all positions
    positions_result = get_positions(wallet_id)
    positions = positions_result.get("positions", [])
    
    if not positions:
        print("\n✅ No open positions found. Nothing to close.")
        return {
            "success": True,
            "closed_count": 0,
            "positions": [],
            "walletAddress": wallet_address,
            "accountId": account_id,
        }
    
    # Filter positions with non-zero quantity
    open_positions = [
        pos for pos in positions 
        if pos.get("position_qty", 0) != 0
    ]
    
    if not open_positions:
        print("\n✅ No open positions found (all positions are flat).")
        return {
            "success": True,
            "closed_count": 0,
            "positions": [],
            "walletAddress": wallet_address,
            "accountId": account_id,
        }
    
    print(f"\n📈 Found {len(open_positions)} open position(s) to close:")
    print("-" * 100)
    
    for idx, pos in enumerate(open_positions, 1):
        symbol = pos.get("symbol", "N/A")
        position_qty = pos.get("position_qty", 0)
        side = "LONG" if position_qty > 0 else "SHORT"
        print(f"{idx}. {symbol} ({side}) - Quantity: {position_qty}")
    
    print("\n🔄 Closing all positions...")
    print("-" * 100)
    
    closed_positions = []
    failed_positions = []
    
    for idx, pos in enumerate(open_positions, 1):
        symbol = pos.get("symbol", "N/A")
        position_qty = pos.get("position_qty", 0)
        abs_qty = abs(position_qty)
        
        # Determine side: SELL to close LONG, BUY to close SHORT
        side = "SELL" if position_qty > 0 else "BUY"
        
        print(f"\n[{idx}/{len(open_positions)}] Closing {symbol} ({side} {abs_qty})...")
        
        try:
            # For MARKET orders on futures/perpetual contracts:
            # Both BUY and SELL orders use order_quantity (base currency)
            order_kwargs = {
                "wallet_id": wallet_id,
                "symbol": symbol,
                "order_type": "MARKET",
                "side": side,
                "reduce_only": True,
                "order_quantity": abs_qty
            }
            
            # Create order to close position
            order_result = create_order(**order_kwargs)
            
            order_id = order_result.get("orderId")
            print(f"   ✅ Order created successfully: Order ID {order_id}")
            
            closed_positions.append({
                "symbol": symbol,
                "side": side,
                "quantity": abs_qty,
                "orderId": order_id,
                "status": "success"
            })
            
            # Small delay between orders to avoid rate limiting
            if idx < len(open_positions):
                time.sleep(0.5)
                
        except Exception as error:
            print(f"   ❌ Failed to close position: {error}")
            failed_positions.append({
                "symbol": symbol,
                "side": side,
                "quantity": abs_qty,
                "error": str(error),
                "status": "failed"
            })
    
    print("\n" + "=" * 100)
    print("\n📝 Closing Summary:")
    print(f"   Total Positions: {len(open_positions)}")
    print(f"   Successfully Closed: {len(closed_positions)}")
    print(f"   Failed: {len(failed_positions)}")
    
    if closed_positions:
        print("\n✅ Successfully Closed Positions:")
        for pos in closed_positions:
            print(f"   - {pos['symbol']}: {pos['side']} {pos['quantity']} (Order ID: {pos['orderId']})")
    
    if failed_positions:
        print("\n❌ Failed to Close Positions:")
        for pos in failed_positions:
            print(f"   - {pos['symbol']}: {pos['side']} {pos['quantity']} - Error: {pos['error']}")
    
    return {
        "success": len(failed_positions) == 0,
        "closed_count": len(closed_positions),
        "failed_count": len(failed_positions),
        "closed_positions": closed_positions,
        "failed_positions": failed_positions,
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Close all open positions for an Orderly account using MARKET orders")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    
    args = parser.parse_args()
    
    try:
        result = close_all_positions(
            wallet_id=args.wallet_id
        )
        
        if result["success"]:
            print("\n✅ All positions closed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Closed {result['closed_count']} positions, but {result['failed_count']} failed.")
            sys.exit(1)
            
    except Exception as error:
        print(f"\n❌ Failed to close positions: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
