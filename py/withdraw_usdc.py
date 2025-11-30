"""
Withdraw funds from Orderly account using Privy agentic wallet
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/withdrawal-deposit
"""
import os
import sys
import argparse
import time
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
CHAIN_ID = int(os.getenv("CHAIN_ID", "80001"))
BROKER_ID = "woofi_pro"
WITHDRAW_VERIFYING_CONTRACT = "0x6F7a338F2aA472838dEFD3283eB360d4Dff5D203"

# Token decimals mapping
TOKEN_DECIMALS = {
    "USDC": 6,
    "USDT": 6,
    "DAI": 18,
    "WETH": 18,
    "ETH": 18,
}

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


def sign_typed_data(wallet_id: str, typed_data: dict, app_id: str, app_secret: str, authorization_secret: str) -> str:
    """Sign EIP-712 typed data using Privy"""
    auth_string = f"{app_id}:{app_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "privy-app-id": app_id,
        "Content-Type": "application/json"
    }
    payload = {
        "authorization_context": {"authorization_private_keys": [authorization_secret]},
        "params": {"typed_data": typed_data}
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


def get_withdrawal_nonce(account_id: str, orderly_key: str, orderly_private_key: bytes) -> int:
    """Get withdrawal nonce from Orderly API"""
    path = "/v1/withdraw_nonce"
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
        raise Exception(f"Failed to get withdrawal nonce: {data}")
    
    return (
        data.get("data", {}).get("withdraw_nonce") or
        data.get("data", {}).get("nonce") or
        data.get("withdrawNonce") or
        data.get("nonce")
    )


def withdraw_funds(wallet_id: str, wallet_address: str = None, amount: str = None, token: str = "USDC", chain_id: int = None) -> dict:
    """Withdraw funds from Orderly account"""
    app_id = os.getenv("PRIVY_APP_ID")
    app_secret = os.getenv("PRIVY_APP_SECRET")
    authorization_secret = os.getenv("PRIVY_AUTHORIZATION_SECRET")
    orderly_key = os.getenv("ORDERLY_KEY")
    orderly_private_key_hex = os.getenv("ORDERLY_PRIVATE_KEY")
    
    if not app_id or not app_secret:
        raise ValueError("Missing PRIVY_APP_ID or PRIVY_APP_SECRET")
    if not authorization_secret:
        raise ValueError("Missing PRIVY_AUTHORIZATION_SECRET")
    if not wallet_id:
        raise ValueError("Wallet ID is required")
    if not amount:
        raise ValueError("Amount is required")
    if not orderly_key:
        raise ValueError("ORDERLY_KEY environment variable is required")
    if not orderly_private_key_hex:
        raise ValueError("ORDERLY_PRIVATE_KEY environment variable is required")
    
    orderly_private_key = hex_to_private_key(orderly_private_key_hex)
    
    chain_id = chain_id or CHAIN_ID
    chain_id_hex = f"0x{chain_id:x}"
    token = token.upper()
    
    if not wallet_address:
        print("Fetching wallet details...")
        wallet_address = get_wallet_address(wallet_id, app_id, app_secret)
        print(f"   Wallet Address: {wallet_address}")
    
    account_id = get_account_id(wallet_address, BROKER_ID)
    
    print("\nPreparing withdrawal from Orderly...")
    print(f"   Wallet ID: {wallet_id}")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   Amount: {amount} {token}")
    print(f"   Chain ID: {chain_id} ({chain_id_hex})")
    print(f"   Account ID: {account_id}")
    
    # Step 1: Get withdrawal nonce
    print("\nStep 1: Fetching withdrawal nonce...")
    withdraw_nonce = get_withdrawal_nonce(account_id, orderly_key, orderly_private_key)
    print(f"   Withdrawal nonce: {withdraw_nonce}")
    
    # Step 2: Convert amount
    token_decimals = TOKEN_DECIMALS.get(token, 18)
    print(f"\nStep 2: Converting amount...")
    print(f"   Token: {token}, Decimals: {token_decimals}")
    amount_in_smallest_unit = int(float(amount) * (10 ** token_decimals))
    print(f"   Amount: {amount} {token} = {amount_in_smallest_unit} (smallest unit)")
    
    # Step 3: Create EIP-712 message
    timestamp = int(time.time() * 1000)
    message = {
        "brokerId": BROKER_ID,
        "chainId": chain_id,
        "receiver": wallet_address,
        "token": token,
        "amount": str(amount_in_smallest_unit),
        "withdrawNonce": str(withdraw_nonce),
        "timestamp": str(timestamp),
    }
    
    print("\nStep 3: Creating EIP-712 message...")
    print(f"Message: {message}")
    
    # Step 4: Create EIP-712 domain
    domain = {
        "name": "Orderly",
        "version": "1",
        "chainId": chain_id_hex,
        "verifyingContract": WITHDRAW_VERIFYING_CONTRACT,
    }
    
    # Step 5: Create EIP-712 types
    typed_data = {
        "domain": domain,
        "message": message,
        "primary_type": "Withdraw",
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Withdraw": [
                {"name": "brokerId", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "receiver", "type": "address"},
                {"name": "token", "type": "string"},
                {"name": "amount", "type": "uint256"},
                {"name": "withdrawNonce", "type": "uint64"},
                {"name": "timestamp", "type": "uint64"},
            ],
        },
    }
    
    # Step 6: Sign the EIP-712 message
    print("\nStep 4: Signing EIP-712 message...")
    signature = sign_typed_data(wallet_id, typed_data, app_id, app_secret, authorization_secret)
    print(f"\n✅ Signature generated: {signature}")
    
    # Step 7: Create withdraw request
    print("\nStep 5: Creating withdrawal request...")
    path = "/v1/withdraw_request"
    
    request_body = {
        "message": {
            "brokerId": message["brokerId"],
            "chainId": message["chainId"],
            "receiver": message["receiver"],
            "token": message["token"],
            "amount": message["amount"],
            "withdrawNonce": message["withdrawNonce"],
            "timestamp": message["timestamp"],
        },
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
        raise Exception(f"Withdrawal request failed: {data}")
    
    if not data.get("success"):
        raise Exception(f"Withdrawal request failed: {data}")
    
    print("\n✅ Withdrawal request successful!")
    print(f"Response: {data}")
    
    return {
        "success": True,
        "data": data,
        "userAddress": wallet_address,
        "amount": amount,
        "token": token,
        "targetChainId": chain_id,
        "withdrawNonce": withdraw_nonce,
    }


def main():
    parser = argparse.ArgumentParser(description="Withdraw funds from Orderly account")
    parser.add_argument("--wallet-id", required=True, help="Privy wallet ID to use (required)")
    parser.add_argument("--wallet-address", help="Wallet address (optional, will be fetched if not provided)")
    parser.add_argument("--amount", required=True, help="Amount to withdraw (required, e.g., '100')")
    parser.add_argument("--token", default="USDC", help="Token symbol to withdraw (optional, default: 'USDC')")
    parser.add_argument("--chain-id", type=int, help="Chain ID (optional, default: 80001 = Polygon Mumbai)")
    
    args = parser.parse_args()
    
    # Validate minimum withdrawal amount
    if args.amount:
        amount_num = float(args.amount)
        if amount_num < 1.001:
            print(f"Error: Withdrawal amount must be at least 1.001. Got: {args.amount}")
            sys.exit(1)
    
    try:
        result = withdraw_funds(
            wallet_id=args.wallet_id,
            wallet_address=args.wallet_address,
            amount=args.amount,
            token=args.token,
            chain_id=args.chain_id
        )
        
        print("\n📝 Withdrawal Summary:")
        print(f"   Wallet Address: {result['userAddress']}")
        print(f"   Amount: {result['amount']} {result['token']}")
        print(f"   Target Chain ID: {result['targetChainId']}")
        print(f"   Withdrawal Nonce: {result['withdrawNonce']}")
        print("\nNote: The withdrawal will be processed by Orderly Network.")
        print("Check your wallet on the target chain after processing completes.")
        
        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to withdraw funds: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

