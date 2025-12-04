"""
Get current holding from Orderly account
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-current-holding
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


def get_holding(wallet_id: str) -> dict:
    """
    Get current holding from Orderly account
    
    Args:
        wallet_id: The Privy wallet ID (required)
        
    Returns:
        Holding result
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
    
    print("\nFetching current holding from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Broker ID: {BROKER_ID}")
    print(f"   Account ID: {account_id}")
    
    # Build query parameters
    path = "/v1/client/holding"
    
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
        raise Exception(f"Failed to get holding: {data}")
    
    if not data.get("success"):
        raise Exception(f"Orderly API returned error: {data}")
    
    print("\n✅ Holding retrieved successfully!")
    
    return {
        "success": True,
        "data": data.get("data"),
        "holdings": data.get("data", {}).get("holding", []),
        "timestamp": data.get("timestamp"),
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def get_holding_async(wallet_id: str) -> dict:
    """Alternative version of get_holding (kept for compatibility)"""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    
    # Get Orderly keys from database
    orderly_key, orderly_private_key_hex = get_orderly_keys_or_raise(wallet_id)
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nFetching current holding from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    
    path = "/v1/client/holding"
    
    request_config = create_authenticated_request(
        "GET",
        path,
        None,
        account_id,
        orderly_key,
        orderly_private_key
    )
    
    response = requests.get(
        f"{ORDERLY_API_URL}{path}",
        headers=request_config["headers"]
    )
    
    data = response.json()
    
    if not response.ok:
        raise Exception(f"Failed to get holding: {data}")
    
    if not data.get("success"):
        raise Exception(f"Orderly API returned error: {data}")
    
    print("\n✅ Holding retrieved successfully!")
    
    return {
        "success": True,
        "data": data.get("data"),
        "holdings": data.get("data", {}).get("holding", []),
        "timestamp": data.get("timestamp"),
        "walletAddress": wallet_address,
        "accountId": account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Get current holding from Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    
    args = parser.parse_args()
    
    try:
        result = get_holding(
            wallet_id=args.wallet_id
        )
        
        # Display holdings
        print("\n📊 Current Holdings:")
        print("=" * 80)
        
        if not result["holdings"]:
            print("   No holdings found.")
        else:
            total_holding = 0
            for index, holding in enumerate(result["holdings"], 1):
                available = holding["holding"] - holding["frozen"]
                total_holding += holding["holding"]
                
                print(f"\n{index}. {holding['token']}:")
                print(f"   Total Holding: {holding['holding']:,}")
                print(f"   Frozen: {holding['frozen']:,}")
                print(f"   Available: {available:,}")
                print(f"   Pending Short: {holding.get('pending_short', 0):,}")
                print(f"   Updated: {holding.get('updated_time', 'N/A')}")
            
            print("\n" + "=" * 80)
            print(f"Total Holdings: {total_holding:,} (across all tokens)")
        
        print("\n📝 Summary:")
        print(f"   Wallet Address: {result['walletAddress']}")
        print(f"   Account ID: {result['accountId']}")
        print(f"   Number of Tokens: {len(result['holdings'])}")
        print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to get holding: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

