"""
Deposit USDC to Orderly account using Privy agentic wallet
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from web3 import Web3
from eth_utils import keccak, to_hex
from privy import PrivyAPI
from privy_utils import get_account_id, get_wallet_address

from orderly_constants import ORDERLY_API_URL, CHAIN_ID, BROKER_ID

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

# Orderly Vault contract addresses
ORDERLY_VAULT = {
    1: "0x816f722424b49cf1275cc86da9840fbd5a6167e9",
    11155111: "0x0EaC556c0C2321BA25b9DC01e4e3c95aD5CDCd2f",
    42161: "0x816f722424B49Cf1275cc86DA9840Fbd5a6167e9",
    421614: "0x0EaC556c0C2321BA25b9DC01e4e3c95aD5CDCd2f",
    10: "0x816f722424b49cf1275cc86da9840fbd5a6167e9",
    11155420: "0xEfF2896077B6ff95379EfA89Ff903598190805EC",
    8453: "0x816f722424b49cf1275cc86da9840fbd5a6167e9",
    84532: "0xdc7348975aE9334DbdcB944DDa9163Ba8406a0ec",
    5000: "0x816f722424b49cf1275cc86da9840fbd5a6167e9",
    5003: "0xfb0E5f3D16758984E668A3d76f0963710E775503",
    56: "0x816f722424B49Cf1275cc86DA9840Fbd5a6167e9",
    97: "0xaf2036D5143219fa00dDd90e7A2dbF3E36dba050",
    137: "0x816f722424b49cf1275cc86da9840fbd5a6167e9",
    80001: "0x816f722424b49cf1275cc86da9840fbd5a6167e9",
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
        "constant": False,
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
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
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
]

# Vault ABI
VAULT_ABI = [
    {
        "constant": False,
        "inputs": [{
            "components": [
                {"name": "accountId", "type": "bytes32"},
                {"name": "brokerHash", "type": "bytes32"},
                {"name": "tokenHash", "type": "bytes32"},
                {"name": "tokenAmount", "type": "uint128"}
            ],
            "name": "depositData",
            "type": "tuple"
        }],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "account", "type": "address"},
            {
                "components": [
                    {"name": "accountId", "type": "bytes32"},
                    {"name": "brokerHash", "type": "bytes32"},
                    {"name": "tokenHash", "type": "bytes32"},
                    {"name": "tokenAmount", "type": "uint128"}
                ],
                "name": "depositData",
                "type": "tuple"
            }
        ],
        "name": "getDepositFee",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
]



def send_transaction(wallet_id: str, transaction: dict, app_id: str, app_secret: str, authorization_secret: str, chain_id: int) -> dict:
    """Send transaction using PrivyAPI"""
    client = PrivyAPI(
        app_id=app_id,
        app_secret=app_secret
    )
    client.update_authorization_key(authorization_secret)
    
    result = client.wallets.rpc(
        wallet_id=wallet_id,
        method="eth_sendTransaction",
        caip2=f"eip155:{chain_id}",
        params={
            "transaction": transaction
        }
    )
    
    # Normalize response format
    if isinstance(result, dict) and "result" in result:
        return {"transaction_hash": result.get("result"), "hash": result.get("result"), "status": "pending"}
    elif isinstance(result, dict):
        return result
    else:
        return {"transaction_hash": str(result), "hash": str(result), "status": "pending"}


def deposit_usdc(wallet_id: str, amount: str = None, chain_id: int = None) -> dict:
    """Deposit USDC to Orderly account"""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    authorization_secret = os.getenv("PRIVY_AUTHORIZATION_SECRET")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not authorization_secret:
        raise ValueError("Missing PRIVY_AUTHORIZATION_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    if not amount:
        raise ValueError("Amount is required")
    
    chain_id = chain_id or CHAIN_ID
    chain_id_hex = f"0x{chain_id:x}"
    
    # Get wallet address
    print("Fetching wallet details...")
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
    print(f"   Wallet Address: {wallet_address}")
    
    print("\nPreparing USDC deposit to Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Amount: {amount} USDC")
    print(f"   Chain ID: {chain_id} ({chain_id_hex})")
    
    # Get contract addresses
    usdc_address = USDC_ADDRESSES.get(chain_id)
    if not usdc_address:
        raise ValueError(f"USDC address not configured for chain ID {chain_id}")
    
    vault_address = ORDERLY_VAULT.get(chain_id)
    if not vault_address:
        raise ValueError(f"Orderly Vault address not configured for chain ID {chain_id}")
    
    rpc_url = RPC_URLS.get(chain_id)
    if not rpc_url:
        raise ValueError(f"RPC URL not configured for chain ID {chain_id}")
    
    # Create provider
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    usdc_contract = w3.eth.contract(address=usdc_address, abi=ERC20_ABI)
    
    # Get decimals
    decimals = usdc_contract.functions.decimals().call()
    print(f"   USDC decimals: {decimals}")
    
    # Convert amount
    amount_wei = int(float(amount) * (10 ** decimals))
    print(f"   Amount in smallest unit: {amount_wei}")
    
    # Check balance
    balance = usdc_contract.functions.balanceOf(wallet_address).call()
    print(f"   Current USDC balance: {balance / (10 ** decimals)}")
    
    if balance < amount_wei:
        raise ValueError(f"Insufficient balance. Required: {amount}, Available: {balance / (10 ** decimals)}")
    
    # Check and approve if needed
    current_allowance = usdc_contract.functions.allowance(wallet_address, vault_address).call()
    print(f"   Current allowance: {current_allowance / (10 ** decimals)}")
    
    if current_allowance < amount_wei:
        print("\nApproving USDC transfer to Orderly Vault...")
        approve_data = usdc_contract.encode_abi("approve", args=[vault_address, amount_wei])
        
        approve_response = send_transaction(
            wallet_id,
            {"chain_id": chain_id_hex, "to": usdc_address, "data": approve_data},
            app_id,
            app_secret,
            authorization_secret,
            chain_id
        )
        
        tx_hash = approve_response.get("transaction_hash") or approve_response.get("hash")
        print(f"   Approval transaction hash: {tx_hash}")
        print("   Waiting for approval confirmation...")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"   Approval confirmed in block: {receipt['blockNumber']}")
        
        # Verify allowance
        import time
        for i in range(10):
            verified_allowance = usdc_contract.functions.allowance(wallet_address, vault_address).call()
            if verified_allowance >= amount_wei:
                print("   Allowance verified")
                break
            if i == 9:
                raise Exception("Allowance verification failed")
            time.sleep(1)
    else:
        print("   Sufficient allowance already exists")
    
    # Prepare deposit data
    orderly_account_id = get_account_id(wallet_address, BROKER_ID)
    broker_hash = keccak(BROKER_ID.encode())
    token_hash = keccak(b"USDC")
    token_amount = amount_wei & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # uint128
    
    deposit_data = {
        "accountId": orderly_account_id,
        "brokerHash": to_hex(broker_hash),
        "tokenHash": to_hex(token_hash),
        "tokenAmount": token_amount,
    }
    
    print("\nDeposit data prepared:")
    print(f"   Account ID: {orderly_account_id}")
    print(f"   Broker Hash: {to_hex(broker_hash)}")
    print(f"   Token Hash: {to_hex(token_hash)}")
    print(f"   Token Amount: {token_amount}")
    
    # Get deposit fee
    vault_contract = w3.eth.contract(address=vault_address, abi=VAULT_ABI)
    deposit_fee = vault_contract.functions.getDepositFee(wallet_address, deposit_data).call()
    print(f"\nCalculating deposit fee...")
    print(f"   Deposit fee: {deposit_fee / 1e18} ETH")
    
    # Encode deposit function
    deposit_data_encoded = vault_contract.encode_abi("deposit", args=[deposit_data])
    
    # Call deposit
    print(f"\nDepositing {amount} USDC to Orderly Vault...")
    deposit_response = send_transaction(
        wallet_id,
        {
            "chain_id": chain_id_hex,
            "to": vault_address,
            "data": deposit_data_encoded,
            "value": hex(deposit_fee),
        },
        app_id,
        app_secret,
        authorization_secret,
        chain_id
    )
    
    tx_hash = deposit_response.get("transaction_hash") or deposit_response.get("hash")
    print(f"   Transaction hash: {tx_hash}")
    print("   Waiting for transaction confirmation...")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"   Transaction confirmed in block: {receipt['blockNumber']}")
    print("\n✅ USDC deposit successful!")
    
    return {
        "success": True,
        "transactionHash": tx_hash,
        "blockNumber": receipt["blockNumber"],
        "vaultAddress": vault_address,
        "amount": amount,
        "token": "USDC",
        "userAddress": wallet_address,
        "orderlyAccountId": orderly_account_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Deposit USDC to Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--amount", required=True, help="Amount of USDC to deposit (required, e.g., '100')")
    parser.add_argument("--chain-id", type=int, help="Chain ID (optional, default: 80001 = Polygon Mumbai)")
    
    args = parser.parse_args()
    
    try:
        result = deposit_usdc(
            wallet_id=args.wallet_id,
            amount=args.amount,
            chain_id=args.chain_id
        )
        
        print("\n📝 Deposit Summary:")
        print(f"   Wallet Address: {result['userAddress']}")
        print(f"   Transaction Hash: {result['transactionHash']}")
        print(f"   Block Number: {result['blockNumber']}")
        print(f"   Amount: {result['amount']} {result['token']}")
        print(f"   Vault Address: {result['vaultAddress']}")
        print(f"   Orderly Account ID: {result['orderlyAccountId']}")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to deposit USDC: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

