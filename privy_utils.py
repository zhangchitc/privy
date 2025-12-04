"""
Shared utility functions for Privy and Orderly Network integration
"""
from typing import Any, Dict

import base64
import requests
from eth_abi import encode
from eth_utils import keccak, to_hex
from privy_eth_account import create_eth_account, PrivyHTTPClient

# Privy API base URL (used for low-level wallet operations)
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
        "Content-Type": "application/json",
    }
    response = requests.get(f"{PRIVY_API_BASE}/wallets/{wallet_id}", headers=headers)
    if not response.ok:
        raise Exception(f"Failed to get wallet: {response.text}")
    wallet: Dict[str, Any] = response.json()
    wallet_address = (
        wallet.get("address")
        or (wallet.get("addresses", [{}])[0].get("address") if wallet.get("addresses") else None)
        or (wallet.get("addresses", [None])[0] if wallet.get("addresses") else None)
    )
    if not wallet_address:
        raise Exception("Could not determine wallet address from wallet object")
    return wallet_address


def sign_typed_data(
    wallet_id: str,
    typed_data: dict,
    app_id: str,
    app_secret: str,
    authorization_secret: str,
) -> str:
    """
    Sign EIP-712 typed data using Privy + privy-eth-account.

    This mirrors the pattern used for integrating Privy wallets with common Ethereum
    libraries, but on the server side with Python, using the `privy-eth-account`
    helper library (see the Privy Ethereum web3 integrations docs:
    [Privy Ethereum web3 integrations](https://docs.privy.io/wallets/using-wallets/ethereum/web3-integrations#python)).
    """
    # Initialize Privy HTTP client with server-side credentials and authorization key
    client = PrivyHTTPClient(
        app_id=app_id,
        app_secret=app_secret,
        authorization_key=authorization_secret,
    )

    # Fetch the wallet address for this wallet_id
    wallet_address = get_wallet_address(wallet_id, app_id, app_secret)

    # Create an eth_account-style account object backed by Privy
    account = create_eth_account(client, wallet_address, wallet_id)

    signed = account.sign_typed_data(full_message=typed_data)
    # Return the hex signature string
    return signed.signature.hex()

