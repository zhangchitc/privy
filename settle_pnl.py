"""
Settle PnL for an Orderly account
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/settle-pnl
"""
import os
import sys
import argparse
import time
from dotenv import load_dotenv
from orderly_auth import create_authenticated_request, hex_to_private_key
import requests
from privy_utils import get_account_id, get_wallet_address, sign_typed_data
from orderly_constants import ORDERLY_API_URL, CHAIN_ID, BROKER_ID, WITHDRAW_VERIFYING_CONTRACT
from orderly_db import get_orderly_keys_or_raise

load_dotenv()


def get_settle_pnl_nonce(account_id: str, orderly_key: str, orderly_private_key: bytes) -> int:
    """Get settle PnL nonce from Orderly API"""
    path = "/v1/settle_nonce"
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
        raise Exception(f"Failed to get settle PnL nonce: {data}")
    
    if not data.get("success"):
        raise Exception(f"Failed to get settle PnL nonce: {data}")
    
    return data.get("data", {}).get("settle_nonce")


def settle_pnl(wallet_id: str, chain_id: int = None) -> dict:
    """
    Settle PnL for an Orderly account
    
    Args:
        wallet_id: The Privy wallet ID (required)
        chain_id: Chain ID (optional, defaults to CHAIN_ID)
        
    Returns:
        Settlement result
    """
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    authorization_secret = os.getenv("PRIVY_AUTHORIZATION_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not authorization_secret:
        raise ValueError("Missing PRIVY_AUTHORIZATION_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    
    # Get Orderly keys from database
    orderly_key, orderly_private_key_hex = get_orderly_keys_or_raise(wallet_id)
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    chain_id_number = int(chain_id or CHAIN_ID)
    chain_id_hex = f"0x{chain_id_number:x}"
    
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nPreparing PnL settlement...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Account ID: {account_id}")
    print(f"   Chain ID: {chain_id_number} ({chain_id_hex})")
    print(f"   Broker ID: {BROKER_ID}")
    
    # Step 1: Get settle PnL nonce
    print("\nStep 1: Fetching settle PnL nonce...")
    settle_nonce = get_settle_pnl_nonce(account_id, orderly_key, orderly_private_key)
    print(f"   Settle PnL nonce: {settle_nonce}")
    
    # Step 2: Create EIP-712 message
    timestamp = int(time.time() * 1000)  # UNIX milliseconds
    message = {
        "brokerId": BROKER_ID,
        "chainId": chain_id_number,
        "settleNonce": str(settle_nonce),
        "timestamp": str(timestamp),
    }
    
    print("\nStep 2: Creating EIP-712 message...")
    print(f"Message: {message}")
    
    # Step 3: Create EIP-712 domain (using on-chain domain - ledger contract)
    domain = {
        "name": "Orderly",
        "version": "1",
        "chainId": chain_id_hex,
        "verifyingContract": WITHDRAW_VERIFYING_CONTRACT,
    }
    
    # Step 4: Create EIP-712 types
    typed_data = {
        "domain": domain,
        "message": message,
        "primary_type": "SettlePnl",
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "SettlePnl": [
                {"name": "brokerId", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "settleNonce", "type": "uint64"},
                {"name": "timestamp", "type": "uint64"},
            ],
        },
    }
    
    # Step 5: Sign the EIP-712 message
    print("\nStep 3: Signing EIP-712 message...")
    signature = sign_typed_data(wallet_id, typed_data, app_id, app_secret, authorization_secret)
    print(f"\n✅ Signature generated: {signature}")
    
    # Step 6: Request PnL settlement
    print("\nStep 4: Requesting PnL settlement...")
    path = "/v1/settle_pnl"
    
    request_body = {
        "message": message,
        "signature": signature,
        "userAddress": wallet_address,
        "verifyingContract": WITHDRAW_VERIFYING_CONTRACT,
    }
    
    print(f"Request body: {request_body}")
    
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
        raise Exception(f"PnL settlement request failed: {data}")
    
    if not data.get("success"):
        raise Exception(f"PnL settlement request failed: {data}")
    
    print("\n✅ PnL settlement successful!")
    print(f"Response: {data}")
    
    return {
        "success": True,
        "data": data,
        "userAddress": wallet_address,
        "accountId": account_id,
        "settleNonce": settle_nonce,
    }


def main():
    parser = argparse.ArgumentParser(description="Settle PnL for an Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--chain-id", type=int, help="Chain ID (optional, default: 8453 = Base Mainnet)")
    
    args = parser.parse_args()
    
    try:
        result = settle_pnl(
            wallet_id=args.wallet_id,
            chain_id=args.chain_id
        )
        
        print("\n📝 Settlement Summary:")
        print(f"   Wallet Address: {result['userAddress']}")
        print(f"   Account ID: {result['accountId']}")
        print(f"   Settle Nonce: {result['settleNonce']}")
        print("\n✅ PnL has been settled into your USDC balance.")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to settle PnL: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
