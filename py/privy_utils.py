"""
Shared utility functions for Privy and Orderly Network integration
"""
import base64
import requests
from eth_abi import encode
from eth_utils import keccak, to_hex

# Privy API base URL
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

