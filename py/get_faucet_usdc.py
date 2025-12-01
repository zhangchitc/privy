"""
Request USDC from Orderly's testnet faucet.

Docs: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/public/get-faucet-usdctestnet-only

This script calls the EVM faucet endpoint:
  POST https://testnet-operator-evm.orderly.org/v1/faucet/usdc
"""
import argparse
import sys
import requests

from orderly_constants import BROKER_ID

# Testnet faucet endpoint (EVM)
FAUCET_URL = "https://testnet-operator-evm.orderly.org/v1/faucet/usdc"


def get_faucet_usdc(user_address: str, chain_id: str, broker_id: str = None) -> dict:
    """Request USDC from Orderly testnet faucet.

    Args:
        user_address: EVM address to receive faucet USDC (required).
        chain_id: Chain ID string for the target EVM testnet (required).
        broker_id: Orderly broker ID (optional, defaults to BROKER_ID from constants).

    Returns:
        Parsed JSON response from the faucet API.
    """
    if not user_address:
        raise ValueError("user_address is required")
    if not chain_id:
        raise ValueError("chain_id is required")

    broker_id = broker_id or BROKER_ID

    payload = {
        "chain_id": chain_id,
        "user_address": user_address,
        "broker_id": broker_id,
    }

    print("Requesting faucet USDC from Orderly testnet...")
    print(f"   Endpoint   : {FAUCET_URL}")
    print(f"   Chain ID   : {chain_id}")
    print(f"   User Addr  : {user_address}")
    print(f"   Broker ID  : {broker_id}")

    response = requests.post(FAUCET_URL, json=payload)
    data = response.json()

    if not response.ok:
        raise Exception(f"Faucet request failed ({response.status_code}): {data}")

    if not data.get("success"):
        raise Exception(f"Faucet API returned error: {data}")

    print("\n✅ Faucet request successful!")
    print(f"   Timestamp: {data.get('timestamp')}")

    return data


def main():
    parser = argparse.ArgumentParser(description="Get USDC from Orderly testnet faucet")
    parser.add_argument("--user-address", required=True, help="EVM wallet address to receive faucet USDC (required)")
    parser.add_argument(
        "--chain-id",
        required=True,
        help=(
            "Chain ID string for the EVM testnet (required). "
            "Example: '421614' for Arbitrum Sepolia, '80001' for Polygon Mumbai, etc."
        ),
    )
    parser.add_argument(
        "--broker-id",
        help="Orderly broker ID (optional, defaults to BROKER_ID from orderly_constants)",
    )

    args = parser.parse_args()

    try:
        result = get_faucet_usdc(
            user_address=args.user_address,
            chain_id=args.chain_id,
            broker_id=args.broker_id,
        )

        print("\n📝 Faucet Response:")
        print(f"   Success  : {result.get('success')}")
        print(f"   Timestamp: {result.get('timestamp')}")

        sys.exit(0)
    except Exception as error:
        print(f"\n❌ Failed to get faucet USDC: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
