"""
Sends a transaction from an agentic wallet using Privy
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from privy import PrivyAPI

load_dotenv()

# Chain name mapping
CHAIN_NAMES = {
    "1": "Ethereum Mainnet",
    "5": "Goerli (deprecated)",
    "11155111": "Sepolia Testnet",
    "84532": "Base Sepolia",
    "80001": "Polygon Mumbai",
}


def get_chain_name(chain_id: str) -> str:
    """Get human-readable chain name"""
    return CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")


def send_transaction(wallet_id: str, to: str, value: str = "1000000000000000", chain_id: str = "11155111") -> dict:
    """
    Sends a transaction from an agentic wallet using Privy
    
    Args:
        wallet_id: The wallet ID to send from
        to: Recipient address
        value: Amount in wei (optional, defaults to 0.001 ETH)
        chain_id: Chain ID (optional, defaults to Sepolia testnet: 11155111)
        
    Returns:
        The transaction response
    """
    # Validate environment variables
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    authorization_secret = os.getenv("PRIVY_AUTHORIZATION_SECRET")
    
    if not wallet_id:
        raise ValueError("Wallet ID is required. Use --wallet-id <wallet_id>")
    
    if not to:
        raise ValueError("Recipient address is required. Use --to <address>")
    
    # Convert to hex format (Privy requires hex values with "0x" prefix)
    chain_id_hex = f"0x{int(chain_id):x}"
    value_hex = f"0x{int(value):x}"
    
    print("Preparing transaction...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   To: {to}")
    print(f"   Value: {value} wei ({int(value) / 1e18} ETH) = {value_hex}")
    print(f"   Chain ID: {chain_id} ({get_chain_name(chain_id)}) = {chain_id_hex}")
    
    try:
        # Initialize Privy client
        client = PrivyAPI(
            app_id=app_id,
            app_secret=app_secret
        )
        client.update_authorization_key(authorization_secret)
        
        # Send transaction using PrivyAPI
        result = client.wallets.rpc(
            wallet_id=wallet_id,
            method="eth_sendTransaction",
            caip2=f"eip155:{chain_id}",
            params={
                "transaction": {
                    "to": to,
                    "value": value_hex,
                }
            }
        )
        
        print("\n✅ Transaction sent successfully!")
        print(f"Transaction details: {result}")
        
        # Normalize response format
        if isinstance(result, dict) and "result" in result:
            return {"transaction_hash": result.get("result"), "hash": result.get("result"), "status": "pending"}
        elif isinstance(result, dict):
            return result
        else:
            return {"transaction_hash": str(result), "hash": str(result), "status": "pending"}
    except Exception as error:
        print(f"\n❌ Failed to send transaction: {error}")
        raise


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Send a transaction from an agentic wallet")
    parser.add_argument("--wallet-id", required=True, help="Wallet ID to send from (required)")
    parser.add_argument("--to", required=True, help="Recipient Ethereum address (required)")
    parser.add_argument("--value", default="1000000000000000", help="Amount in wei (optional, default: 1000000000000000 = 0.001 ETH)")
    parser.add_argument("--chain-id", default="11155111", help="Chain ID (optional, default: 11155111 = Sepolia testnet)")
    
    args = parser.parse_args()
    
    try:
        result = send_transaction(
            wallet_id=args.wallet_id,
            to=args.to,
            value=args.value,
            chain_id=args.chain_id
        )
        
        print("\n📝 Transaction Summary:")
        print(f"   Transaction Hash: {result.get('transaction_hash') or result.get('hash') or 'N/A'}")
        print(f"   Status: {result.get('status', 'pending')}")
        if result.get("block_number"):
            print(f"   Block Number: {result['block_number']}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to send transaction: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

