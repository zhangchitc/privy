"""
Get all positions info from Orderly account
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-all-positions-info
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
from orderly_db import get_orderly_keys_or_raise

load_dotenv()


def get_positions(wallet_id: str) -> dict:
    """
    Get all positions info from Orderly account
    
    Args:
        wallet_id: The Privy wallet ID (required)
        
    Returns:
        Positions result with all position data
    """
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    
    # Get Orderly keys from database
    orderly_key, orderly_private_key_hex = get_orderly_keys_or_raise(wallet_id)
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    # Get wallet address
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nFetching positions from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Broker ID: {BROKER_ID}")
    print(f"   Account ID: {account_id}")
    
    # Build API path
    path = "/v1/positions"
    
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
        raise Exception(f"Failed to get positions: {data}")
    
    if not data.get("success"):
        raise Exception(f"Orderly API returned error: {data}")
    
    print("\n✅ Positions retrieved successfully!")
    
    return {
        "success": True,
        "data": data.get("data"),
        "positions": data.get("data", {}).get("rows", []),
        "timestamp": data.get("timestamp"),
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Get all positions info from Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    
    args = parser.parse_args()
    
    try:
        result = get_positions(
            wallet_id=args.wallet_id
        )
        
        # Display positions
        print("\n📊 Current Positions:")
        print("=" * 100)
        
        positions_data = result["data"]
        positions = result["positions"]
        
        # Display summary metrics
        if positions_data:
            print(f"\n💰 Account Summary:")
            print(f"   Total Collateral Value: ${positions_data.get('total_collateral_value', 0):,.2f}")
            print(f"   Free Collateral: ${positions_data.get('free_collateral', 0):,.2f}")
            print(f"   Total PnL (24h): ${positions_data.get('total_pnl_24_h', 0):,.2f}")
            print(f"   Margin Ratio: {positions_data.get('margin_ratio', 0):.4f}")
            print(f"   Initial Margin Ratio: {positions_data.get('initial_margin_ratio', 0):.4f}")
            print(f"   Maintenance Margin Ratio: {positions_data.get('maintenance_margin_ratio', 0):.4f}")
        
        if not positions:
            print("\n   No open positions found.")
        else:
            print(f"\n📈 Open Positions ({len(positions)}):")
            print("-" * 100)
            
            for index, position in enumerate(positions, 1):
                symbol = position.get("symbol", "N/A")
                position_qty = position.get("position_qty", 0)
                side = "LONG" if position_qty > 0 else "SHORT" if position_qty < 0 else "FLAT"
                avg_price = position.get("average_open_price", 0)
                mark_price = position.get("mark_price", 0)
                unsettled_pnl = position.get("unsettled_pnl", 0)
                leverage = position.get("leverage", 0)
                
                print(f"\n{index}. {symbol} ({side})")
                print(f"   Position Quantity: {position_qty}")
                print(f"   Average Open Price: ${avg_price:,.2f}")
                print(f"   Mark Price: ${mark_price:,.2f}")
                print(f"   Unsettled PnL: ${unsettled_pnl:,.2f}")
                print(f"   Leverage: {leverage}x")
                
                if position.get("est_liq_price"):
                    print(f"   Estimated Liquidation Price: ${position.get('est_liq_price'):,.2f}")
                
                if position.get("pnl_24_h") is not None:
                    print(f"   PnL (24h): ${position.get('pnl_24_h', 0):,.2f}")
                
                if position.get("fee_24_h") is not None:
                    print(f"   Fee (24h): ${position.get('fee_24_h', 0):,.2f}")
                
                if position.get("pending_long_qty") or position.get("pending_short_qty"):
                    print(f"   Pending Long Qty: {position.get('pending_long_qty', 0)}")
                    print(f"   Pending Short Qty: {position.get('pending_short_qty', 0)}")
        
        print("\n" + "=" * 100)
        print("\n📝 Summary:")
        print(f"   Wallet Address: {result['walletAddress']}")
        print(f"   Account ID: {result['accountId']}")
        print(f"   Number of Positions: {len(positions)}")
        print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to get positions: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

