"""
Add Orderly Key for a Privy wallet
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/wallet-authentication
"""
import os
import sys
import argparse
import time
import base64
from dotenv import load_dotenv
from pathlib import Path
import requests
from nacl.signing import SigningKey
from nacl.utils import random
import base58

load_dotenv()

# Configuration
ORDERLY_API_URL = "https://api.orderly.org"  # or https://testnet-api.orderly.org for testnet
CHAIN_ID = int(os.getenv("CHAIN_ID", "80001"))  # Default: Polygon Mumbai testnet
BROKER_ID = "woofi_pro"
VERIFYING_CONTRACT = "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"

# Privy API base URL
PRIVY_API_BASE = "https://auth.privy.io/api/v1"


def generate_orderly_key():
    """
    Generate an ed25519 key pair and encode the public key
    
    Returns:
        Object with orderlyKey (public key) and privateKeyHex (private key in hex format)
    """
    # Generate ed25519 key pair
    private_key = random(32)
    signing_key = SigningKey(private_key)
    public_key = signing_key.verify_key.encode()
    
    # Encode public key using base58
    encoded_key = base58.b58encode(public_key).decode("utf-8")
    orderly_key = f"ed25519:{encoded_key}"
    
    # Convert private key to hex format for storage
    private_key_hex = private_key.hex()
    
    return {
        "orderlyKey": orderly_key,
        "privateKeyHex": private_key_hex,
    }


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


def update_env_file(orderly_key: str, orderly_private_key_hex: str):
    """Update or append ORDERLY_KEY and ORDERLY_PRIVATE_KEY to .env file"""
    env_path = Path(".env")
    
    # Read existing .env file if it exists
    env_content = ""
    if env_path.exists():
        env_content = env_path.read_text()
    
    # Check if ORDERLY_KEY already exists in .env
    has_orderly_key = any(line.startswith("ORDERLY_KEY=") for line in env_content.splitlines())
    has_orderly_private_key = any(line.startswith("ORDERLY_PRIVATE_KEY=") for line in env_content.splitlines())
    
    lines = env_content.splitlines() if env_content else []
    
    # Update or append ORDERLY_KEY
    if has_orderly_key:
        lines = [line if not line.startswith("ORDERLY_KEY=") else f"ORDERLY_KEY={orderly_key}" for line in lines]
    else:
        if lines and not lines[-1].endswith("\n"):
            lines.append("")
        lines.append(f"ORDERLY_KEY={orderly_key}")
    
    # Update or append ORDERLY_PRIVATE_KEY
    if has_orderly_private_key:
        lines = [line if not line.startswith("ORDERLY_PRIVATE_KEY=") else f"ORDERLY_PRIVATE_KEY={orderly_private_key_hex}" for line in lines]
    else:
        lines.append(f"ORDERLY_PRIVATE_KEY={orderly_private_key_hex}")
    
    # Write back to .env file
    env_path.write_text("\n".join(lines) + "\n")


def add_orderly_key(wallet_id: str, wallet_address: str = None, chain_id: int = None, broker_id: str = None) -> dict:
    """
    Add Orderly Key for a Privy wallet
    
    Args:
        wallet_id: The Privy wallet ID (required)
        wallet_address: The wallet address (optional, will be fetched if not provided)
        chain_id: The chain ID (optional, defaults to CHAIN_ID)
        broker_id: The broker ID (optional, defaults to BROKER_ID)
        
    Returns:
        Result with generated orderlyKey
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
    
    # Configuration
    chain_id = chain_id or CHAIN_ID
    chain_id_hex = f"0x{chain_id:x}"
    broker_id = broker_id or BROKER_ID
    scope = "read,trading"
    expiration_days = 365
    
    try:
        # Get wallet address if not provided
        if not wallet_address:
            print("Fetching wallet details...")
            wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
            print(f"   Wallet Address: {wallet_address}")
        
        print("\nAdding Orderly Key for Privy wallet...")
        print(f"   Wallet ID: {wallet_id}")
        print(f"   Wallet Address: {wallet_address}")
        print(f"   Chain ID: {chain_id} ({chain_id_hex})")
        print(f"   Broker ID: {broker_id}")
        
        # Generate ed25519 key pair
        print("\nGenerating ed25519 key pair...")
        key_pair = generate_orderly_key()
        orderly_key = key_pair["orderlyKey"]
        orderly_private_key_hex = key_pair["privateKeyHex"]
        
        print(f"   Generated Orderly Key: {orderly_key}")
        print(f"   Generated Orderly Private Key: {orderly_private_key_hex}")
        
        # Create EIP-712 message for adding Orderly Key
        timestamp = int(time.time() * 1000)
        expiration = timestamp + expiration_days * 24 * 60 * 60 * 1000  # Convert days to milliseconds
        
        message = {
            "brokerId": broker_id,
            "chainId": chain_id,
            "orderlyKey": orderly_key,
            "scope": scope,
            "timestamp": timestamp,
            "expiration": expiration,
        }
        
        # Create EIP-712 domain
        domain = {
            "name": "Orderly",
            "version": "1",
            "chainId": chain_id_hex,
            "verifyingContract": VERIFYING_CONTRACT,
        }
        
        # Create EIP-712 types
        typed_data = {
            "domain": domain,
            "message": message,
            "primary_type": "AddOrderlyKey",
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "AddOrderlyKey": [
                    {"name": "brokerId", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "orderlyKey", "type": "string"},
                    {"name": "scope", "type": "string"},
                    {"name": "timestamp", "type": "uint64"},
                    {"name": "expiration", "type": "uint64"},
                ],
            },
        }
        
        print("\nSigning EIP-712 message...")
        print(f"Message: {message}")
        
        # Sign the EIP-712 message using Privy
        signature = sign_typed_data(wallet_id, typed_data, app_id, app_secret, authorization_secret)
        print(f"\n✅ Signature generated: {signature}")
        
        # Add Orderly Key
        print("\nAdding Orderly Key to Orderly...")
        response = requests.post(
            f"{ORDERLY_API_URL}/v1/orderly_key",
            headers={"Content-Type": "application/json"},
            json={
                "message": message,
                "signature": signature,
                "userAddress": wallet_address,
            }
        )
        
        data = response.json()
        
        if not response.ok:
            raise Exception(f"Failed to add Orderly Key: {data}")
        
        print("\n✅ Orderly Key added successfully!")
        print(f"Response: {data}")
        
        # Save Orderly Key and Private Key to .env file
        update_env_file(orderly_key, orderly_private_key_hex)
        
        print("\n✅ Saved to .env file:")
        print(f"   ORDERLY_KEY={orderly_key}")
        print(f"   ORDERLY_PRIVATE_KEY={orderly_private_key_hex}")
        
        return {
            "success": True,
            "data": data,
            "userAddress": wallet_address,
            "orderlyKey": orderly_key,
            "orderlyPrivateKeyHex": orderly_private_key_hex,
        }
    except Exception as error:
        print(f"\n❌ Failed to add Orderly Key: {error}")
        raise


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Add Orderly Key for a Privy wallet")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--wallet-address", help="Wallet address (optional, will be fetched if not provided)")
    parser.add_argument("--chain-id", type=int, help="Chain ID (optional, default: 80001 = Polygon Mumbai)")
    
    args = parser.parse_args()
    
    try:
        result = add_orderly_key(
            wallet_id=args.wallet_id,
            wallet_address=args.wallet_address,
            chain_id=args.chain_id
        )
        
        print("\n📝 Summary:")
        print(f"   Wallet Address: {result['userAddress']}")
        print(f"   Orderly Key: {result['orderlyKey']}")
        print(f"   Orderly Private Key: {result['orderlyPrivateKeyHex']}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to add Orderly Key: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

