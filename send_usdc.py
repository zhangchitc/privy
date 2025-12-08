"""
Sends USDC from an agentic wallet to any given wallet address using Privy
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from web3 import Web3
from privy import PrivyAPI
from privy_utils import get_wallet_address

load_dotenv()

# USDC token addresses
USDC_ADDRESSES = {
    1: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    11155111: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    42161: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    421614: "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d",
    10: "0x0b2c639c533813f4aa9d7837caf62653d097ff85",
    11155420: "0x5fd84259d66Cd46123540766Be93DFE6D43130D7",
    8453: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    84532: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    5000: "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9",
    5003: "0xAcab8129E2cE587fD203FD770ec9ECAFA2C88080",
    56: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
    97: "0x31873b5804bABE258d6ea008f55e08DD00b7d51E",
    137: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    80001: "0x41e94eb019c0762f9bfcf9fb1f3f082b1e1e2079",
}

# RPC URLs
RPC_URLS = {
    1: "https://rpc.ankr.com/eth",
    11155111: "https://rpc.ankr.com/eth_sepolia",
    42161: "https://arb1.arbitrum.io/rpc",
    421614: "https://sepolia-rollup.arbitrum.io/rpc",
    10: "https://mainnet.optimism.io",
    11155420: "https://sepolia.optimism.io",
    8453: "https://mainnet.base.org",
    84532: "https://sepolia.base.org",
    5000: "https://rpc.mantle.xyz",
    5003: "https://rpc.sepolia.mantle.xyz",
    56: "https://bsc-dataseed.binance.org/",
    97: "https://data-seed-prebsc-1-s1.binance.org:8545/",
    137: "https://polygon-rpc.com",
    80001: "https://rpc.ankr.com/polygon_mumbai",
}

# Chain name mapping
CHAIN_NAMES = {
    1: "Ethereum Mainnet",
    5: "Goerli (deprecated)",
    11155111: "Sepolia Testnet",
    84532: "Base Sepolia",
    80001: "Polygon Mumbai",
    42161: "Arbitrum One",
    421614: "Arbitrum Sepolia",
    10: "Optimism Mainnet",
    11155420: "Optimism Sepolia",
    8453: "Base Mainnet",
    5000: "Mantle Mainnet",
    5003: "Mantle Sepolia",
    56: "BNB Smart Chain Mainnet",
    97: "BNB Smart Chain Testnet",
    137: "Polygon Mainnet",
}

# ERC20 ABI
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
]


def get_chain_name(chain_id: int) -> str:
    """Get human-readable chain name"""
    return CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")


def send_usdc(wallet_id: str, to: str, amount: str, chain_id: str = "11155111") -> dict:
    """
    Sends USDC from an agentic wallet to any given wallet address using Privy
    
    Args:
        wallet_id: The wallet ID to send from
        to: Recipient address
        amount: Amount of USDC in human-readable format (e.g., "100")
        chain_id: Chain ID (optional, defaults to Sepolia testnet: 11155111)
        
    Returns:
        The transaction response
    """
    # Validate environment variables
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    authorization_secret = os.getenv("PRIVY_AUTHORIZATION_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError(
            "Missing required environment variables. Please ensure the following are set in your .env file:\n"
            "- PRIVY_APP_ID\n"
            "- PRIVY_APP_SECRET"
        )
    
    if not authorization_secret:
        raise ValueError(
            "Missing authorization credentials. Please ensure the following are set in your .env file:\n"
            "- PRIVY_AUTHORIZATION_SECRET"
        )
    
    if not wallet_id:
        raise ValueError("Wallet ID is required. Use --wallet-id <wallet_id>")
    
    if not to:
        raise ValueError("Recipient address is required. Use --to <address>")
    
    if not amount:
        raise ValueError("Amount is required. Use --amount <amount>")
    
    # Convert chain_id to integer
    chain_id_int = int(chain_id)
    chain_id_hex = f"0x{chain_id_int:x}"
    
    # Initialize Privy client
    client = PrivyAPI(
        app_id=app_id,
        app_secret=app_secret
    )
    client.update_authorization_key(authorization_secret)
    
    try:
        # Get wallet address using the proven helper function
        # This works with both PrivyAPI and direct REST calls
        print("Fetching wallet details...")
        wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
        print(f"   Wallet Address: {wallet_address}")
        
        # Get USDC contract address for the chain
        usdc_address = USDC_ADDRESSES.get(chain_id_int)
        if not usdc_address:
            raise ValueError(
                f"USDC address not configured for chain ID {chain_id_int}. Please update USDC_ADDRESSES."
            )
        
        # Get RPC URL
        rpc_url = RPC_URLS.get(chain_id_int)
        if not rpc_url:
            raise ValueError(
                f"RPC URL not configured for chain ID {chain_id_int}. Please update RPC_URLS in the script."
            )
        
        # Create provider for reading contract state
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        usdc_contract = w3.eth.contract(address=usdc_address, abi=ERC20_ABI)
        
        # Get USDC decimals
        decimals = usdc_contract.functions.decimals().call()
        
        # Convert amount to wei/smallest unit
        amount_wei = int(float(amount) * (10 ** decimals))
        
        # Check balance
        balance = usdc_contract.functions.balanceOf(wallet_address).call()
        balance_formatted = balance / (10 ** decimals)
        
        print("\nPreparing USDC transfer...")
        print(f"   Wallet ID: {wallet_id}")
        print(f"   Wallet Address: {wallet_address}")
        print(f"   Recipient: {to}")
        print(f"   Amount: {amount} USDC")
        print(f"   Amount (smallest unit): {amount_wei}")
        print(f"   Current USDC balance: {balance_formatted}")
        print(f"   Chain ID: {chain_id} ({get_chain_name(chain_id_int)}) = {chain_id_hex}")
        print(f"   USDC Contract: {usdc_address}")
        
        if balance < amount_wei:
            raise ValueError(
                f"Insufficient USDC balance. Required: {amount}, Available: {balance_formatted}"
            )
        
        # Encode transfer function call
        transfer_data = usdc_contract.encode_abi("transfer", args=[w3.to_checksum_address(to), amount_wei])
        
        print("\nSending USDC transfer transaction...")
        
        # Send transaction using PrivyAPI
        # Based on Privy Python SDK documentation:
        # https://docs.privy.io/basics/python/quickstart
        # https://docs.privy.io/recipes/send-usdc#sending-usdc-or-other-erc-20s
        # 
        # For agentic wallets, we use the rpc method with eth_sendTransaction
        # The authorization_context should be included in params for agentic wallets
        result = client.wallets.rpc(
            wallet_id=wallet_id,
            method="eth_sendTransaction",
            caip2=f"eip155:{chain_id}",
            params={
                "transaction": {
                    "to": usdc_address,
                    "data": transfer_data,  # ERC20 transfer function call
                },
            }
        )
        
        print("\n✅ USDC transfer transaction sent successfully!")
        print(f"Transaction details: {result}")
        
        return {"transaction_hash": str(result), "hash": str(result), "status": "pending"}
    except Exception as error:
        print(f"\n❌ Failed to send USDC: {error}")
        raise


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Send USDC from an agentic wallet to any given wallet address")
    parser.add_argument("--wallet-id", required=True, help="Wallet ID to send from (required)")
    parser.add_argument("--to", required=True, help="Recipient Ethereum address (required)")
    parser.add_argument("--amount", required=True, help="Amount of USDC to send (required, e.g., '100')")
    parser.add_argument("--chain-id", default="11155111", help="Chain ID (optional, default: 11155111 = Sepolia testnet)")
    
    args = parser.parse_args()
    
    try:
        result = send_usdc(
            wallet_id=args.wallet_id,
            to=args.to,
            amount=args.amount,
            chain_id=args.chain_id
        )
        
        print("\n📝 Transaction Summary:")
        print(f"   Transaction Hash: {result.get('transaction_hash') or result.get('hash') or 'N/A'}")
        print(f"   Status: {result.get('status', 'pending')}")
        if result.get("block_number"):
            print(f"   Block Number: {result['block_number']}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to send USDC: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
