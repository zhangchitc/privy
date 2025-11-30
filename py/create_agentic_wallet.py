"""
Creates an Agentic wallet using Privy
"""
import os
import sys
import argparse
import base64
from dotenv import load_dotenv
import requests

load_dotenv()

# Privy API base URL
PRIVY_API_BASE = "https://auth.privy.io/api/v1"


def create_agentic_wallet(policy_id: str = None, chain_type: str = "ethereum") -> dict:
    """
    Creates an Agentic wallet using Privy
    
    Args:
        policy_id: Optional policy ID to assign to the wallet
        chain_type: Chain type ('ethereum' or 'solana'), defaults to 'ethereum'
        
    Returns:
        The created wallet object
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
    
    # Prepare wallet creation data
    wallet_data = {
        "chain_type": chain_type,
        "owner_id": authorization_id,
    }
    
    if policy_id:
        wallet_data["policy_ids"] = [policy_id]
    
    print("Creating agentic wallet...")
    print(f"Wallet configuration: {wallet_data}")
    
    # Create the agentic wallet using Privy API
    auth_string = f"{app_id}:{app_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "privy-app-id": app_id,
        "Content-Type": "application/json",
    }
    
    response = requests.post(
        f"{PRIVY_API_BASE}/wallets",
        headers=headers,
        json=wallet_data
    )
    
    if not response.ok:
        raise Exception(f"Failed to create wallet: {response.text}")
    
    wallet = response.json()
    
    print("✅ Agentic wallet created successfully!")
    print(f"Wallet details: {wallet}")
    
    return wallet


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Create an agentic wallet using Privy")
    parser.add_argument("--policy-id", help="Policy ID to assign to the wallet")
    parser.add_argument("--chain-type", default="ethereum", choices=["ethereum", "solana"],
                       help="Chain type (default: ethereum)")
    
    args = parser.parse_args()
    
    try:
        wallet = create_agentic_wallet(
            policy_id=args.policy_id,
            chain_type=args.chain_type
        )
        
        print("\n📝 Wallet Summary:")
        print(f"   Wallet ID: {wallet.get('id') or wallet.get('wallet_id') or 'N/A'}")
        print(f"   Address: {wallet.get('address') or (wallet.get('addresses', [{}])[0] if wallet.get('addresses') else 'N/A')}")
        print(f"   Owner ID: {wallet.get('owner_id', 'N/A')}")
        print(f"   Chain Type: {wallet.get('chain_type', 'N/A')}")
        if wallet.get("policy_ids"):
            print(f"   Policy IDs: {', '.join(wallet['policy_ids'])}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to create agentic wallet: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

