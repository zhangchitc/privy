"""
Registers an account on Orderly Network using a Privy agentic wallet
"""
import os
import sys
import argparse
import time
import base64
from dotenv import load_dotenv
import requests

load_dotenv()

# Configuration
ORDERLY_API_URL = "https://api.orderly.org"  # or https://testnet-api.orderly.org for testnet
BROKER_ID = "woofi_pro"
VERIFYING_CONTRACT = "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"

# Privy API base URL
PRIVY_API_BASE = "https://auth.privy.io/api/v1"


def get_wallet_address(wallet_id: str, app_id: str, app_secret: str) -> str:
    """Get wallet address from Privy"""
    auth_string = f"{app_id}:{app_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "privy-app-id": app_id,
        "Content-Type": "application/json",
    }
    
    response = requests.get(
        f"{PRIVY_API_BASE}/wallets/{wallet_id}",
        headers=headers
    )
    
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


def sign_typed_data(wallet_id: str, typed_data: dict, app_id: str, app_secret: str, authorization_secret: str) -> str:
    """Sign EIP-712 typed data using Privy"""
    auth_string = f"{app_id}:{app_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "privy-app-id": app_id,
        "Content-Type": "application/json",
    }
    
    payload = {
        "authorization_context": {
            "authorization_private_keys": [authorization_secret]
        },
        "params": {
            "typed_data": typed_data
        }
    }
    
    response = requests.post(
        f"{PRIVY_API_BASE}/wallets/{wallet_id}/ethereum/sign-typed-data",
        headers=headers,
        json=payload
    )
    
    if not response.ok:
        raise Exception(f"Failed to sign typed data: {response.text}")
    
    result = response.json()
    return result.get("signature")


def register_orderly_account(wallet_id: str, wallet_address: str = None, chain_id: str = "421614") -> dict:
    """
    Registers an account on Orderly Network using a Privy agentic wallet
    
    Args:
        wallet_id: The wallet ID to use for registration
        wallet_address: The wallet address (optional, will be fetched if not provided)
        chain_id: Chain ID (optional, defaults to 421614 for Arbitrum Sepolia)
        
    Returns:
        The registration response
    """
    # Validate environment variables
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    authorization_id = os.getenv("PRIVY_AUTHORIZATION_ID")
    authorization_secret = os.getenv("PRIVY_AUTHORIZATION_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError(
            "Missing required environment variables. Please ensure the following are set in your .env file:\n"
            "- PRIVY_APP_ID\n"
            "- PRIVY_APP_SECRET"
        )
    
    if not authorization_id or not authorization_secret:
        raise ValueError(
            "Missing authorization credentials. Please ensure the following are set in your .env file:\n"
            "- PRIVY_AUTHORIZATION_ID\n"
            "- PRIVY_AUTHORIZATION_SECRET"
        )
    
    if not wallet_id:
        raise ValueError("Wallet ID is required. Use --wallet-id <wallet_id>")
    
    try:
        # Get wallet address if not provided
        if not wallet_address:
            print("Fetching wallet details...")
            wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
            print(f"   Wallet Address: {wallet_address}")
        
        chain_id_number = int(chain_id)
        chain_id_hex = f"0x{chain_id_number:x}"
        
        print("\nPreparing Orderly account registration...")
        print(f"   Wallet ID: {wallet_id}")
        print(f"   Wallet Address: {wallet_address}")
        print(f"   Chain ID: {chain_id} ({chain_id_hex})")
        print(f"   Broker ID: {BROKER_ID}")
        print(f"   Orderly API: {ORDERLY_API_URL}")
        
        # Step 1: Get registration nonce from Orderly
        print("\nStep 1: Getting registration nonce...")
        nonce_response = requests.get(f"{ORDERLY_API_URL}/v1/registration_nonce")
        if not nonce_response.ok:
            raise Exception(f"Failed to get registration nonce ({nonce_response.status_code}): {nonce_response.text}")
        
        nonce_data = nonce_response.json()
        registration_nonce = nonce_data["data"]["registration_nonce"]
        print(f"   Registration Nonce: {registration_nonce}")
        
        # Step 2: Prepare EIP-712 typed data for Orderly registration
        timestamp = int(time.time() * 1000)  # UNIX milliseconds
        register_message = {
            "brokerId": BROKER_ID,
            "chainId": chain_id_number,
            "timestamp": timestamp,
            "registrationNonce": registration_nonce,
        }
        
        # EIP-712 types structure
        typed_data = {
            "domain": {
                "name": "Orderly",
                "version": "1",
                "chainId": chain_id_hex,
                "verifyingContract": VERIFYING_CONTRACT,
            },
            "message": register_message,
            "primary_type": "Registration",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Registration": [
                    {"name": "brokerId", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "timestamp", "type": "uint64"},
                    {"name": "registrationNonce", "type": "uint256"},
                ],
            },
        }
        
        print("\nStep 2: Signing EIP-712 message...")
        print(f"Register message: {register_message}")
        
        # Step 3: Sign the typed data using Privy
        signature = sign_typed_data(wallet_id, typed_data, app_id, app_secret, authorization_secret)
        print(f"\n✅ Signature generated: {signature}")
        
        # Step 4: Register with Orderly API
        print("\nStep 3: Registering account with Orderly...")
        registration_payload = {
            "message": register_message,
            "signature": signature,
            "userAddress": wallet_address,
        }
        
        print(f"Registration payload: {registration_payload}")
        
        response = requests.post(
            f"{ORDERLY_API_URL}/v1/register_account",
            headers={"Content-Type": "application/json"},
            json=registration_payload
        )
        
        if not response.ok:
            raise Exception(f"Orderly API error ({response.status_code}): {response.text}")
        
        result = response.json()
        
        if not result.get("success"):
            raise Exception(f"Orderly registration failed: {result.get('message', 'Unknown error')}")
        
        orderly_account_id = result["data"]["account_id"]
        print("\n✅ Account registered successfully with Orderly!")
        print(f"Registration response: {result}")
        print(f"\n📝 Orderly Account ID: {orderly_account_id}")
        
        return {
            "signature": signature,
            "walletAddress": wallet_address,
            "orderlyAccountId": orderly_account_id,
            "registration": result,
        }
    except Exception as error:
        print(f"\n❌ Failed to register Orderly account: {error}")
        raise


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Register an account on Orderly Network")
    parser.add_argument("--wallet-id", required=True, help="Wallet ID to use for registration")
    parser.add_argument("--wallet-address", help="Wallet address (optional, will be fetched if not provided)")
    parser.add_argument("--chain-id", default="421614", help="Chain ID (optional, default: 421614 = Arbitrum Sepolia)")
    
    args = parser.parse_args()
    
    try:
        result = register_orderly_account(
            wallet_id=args.wallet_id,
            wallet_address=args.wallet_address,
            chain_id=args.chain_id
        )
        
        print("\n📝 Registration Summary:")
        print(f"   Wallet Address: {result['walletAddress']}")
        print(f"   Orderly Account ID: {result.get('orderlyAccountId', 'N/A')}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to register Orderly account: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

