"""
Get current holding from Orderly account
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-current-holding
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


def get_holding(wallet_id: str, wallet_address: str = None, all: bool = False) -> dict:
    """
    Get current holding from Orderly account
    
    Args:
        wallet_id: The Privy wallet ID (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        all: If true, return all tokens even if balance is empty (optional, default: false)
        
    Returns:
        Holding result
    """
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
    
    # Get wallet address if not provided
    if not wallet_address:
        print("Fetching wallet details...")
        wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
        print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nFetching current holding from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Broker ID: {BROKER_ID}")
    print(f"   Account ID: {account_id}")
    print(f"   Include all tokens: {all}")
    
    # Build query parameters
    query_params = "?all=true" if all else ""
    path = f"/v1/client/holding{query_params}"
    
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


def get_holding_async(wallet_id: str, wallet_address: str = None, all: bool = False) -> dict:
    """Alternative version of get_holding (kept for compatibility)"""
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
    
    print("\nFetching current holding from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    
    query_params = "?all=true" if all else ""
    path = f"/v1/client/holding{query_params}"
    
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
    parser.add_argument("--wallet-address", help="Wallet address (optional, will be fetched if not provided)")
    parser.add_argument("--all", action="store_true", help="Include all tokens even if balance is empty")
    
    args = parser.parse_args()
    
    try:
        result = get_holding(
            wallet_id=args.wallet_id,
            wallet_address=args.wallet_address,
            all=args.all
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

