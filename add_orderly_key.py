"""
Add Orderly Key for a Privy wallet
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/wallet-authentication
"""
import os
import sys
import argparse
import time
from dotenv import load_dotenv
import requests
from nacl.signing import SigningKey
from nacl.utils import random
import base58
from privy_utils import get_wallet_address, sign_typed_data, PRIVY_API_BASE
from orderly_constants import ORDERLY_API_URL, CHAIN_ID, BROKER_ID, VERIFYING_CONTRACT
from orderly_db import save_orderly_keys

load_dotenv()


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




def add_orderly_key(wallet_id: str, chain_id: int = None, broker_id: str = None) -> dict:
    """
    Add Orderly Key for a Privy wallet
    
    Args:
        wallet_id: The Privy wallet ID (required)
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
        # Get wallet address
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
        
        # Save Orderly Key and Private Key to database
        save_orderly_keys(wallet_id, orderly_key, orderly_private_key_hex)
        
        print("\n✅ Saved to database:")
        print(f"   Wallet ID: {wallet_id}")
        print(f"   ORDERLY_KEY={orderly_key}")
        
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
    parser.add_argument("--chain-id", type=int, help="Chain ID (optional, default: 80001 = Polygon Mumbai)")
    
    args = parser.parse_args()
    
    try:
        result = add_orderly_key(
            wallet_id=args.wallet_id,
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

