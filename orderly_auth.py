"""
Orderly Network authentication helper module
Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/api-authentication
"""
import base64
import json
from typing import Optional, Dict, Any
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder


def hex_to_private_key(hex_key: str) -> bytes:
    """
    Convert hex string to bytes private key
    
    Args:
        hex_key: Private key in hex format
        
    Returns:
        Private key as bytes
    """
    # Remove '0x' prefix if present
    clean_hex = hex_key[2:] if hex_key.startswith("0x") else hex_key
    return bytes.fromhex(clean_hex)


def get_content_type(method: str) -> str:
    """
    Get Content-Type header based on HTTP method
    
    Args:
        method: HTTP method
        
    Returns:
        Content-Type value
    """
    upper_method = method.upper()
    if upper_method in ("GET", "DELETE"):
        return "application/x-www-form-urlencoded"
    return "application/json"


def create_authenticated_request(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]],
    account_id: str,
    orderly_key: str,
    orderly_private_key: bytes
) -> Dict[str, Any]:
    """
    Create authenticated request configuration for Orderly API
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., "/v1/withdraw_nonce")
        body: Request body (None for GET requests)
        account_id: Orderly account ID
        orderly_key: Orderly public key (ed25519:...)
        orderly_private_key: Orderly private key (32 bytes)
        
    Returns:
        Request configuration with headers
    """
    import time
    
    timestamp = str(int(time.time() * 1000))
    message = timestamp + method + path + (json.dumps(body) if body else "")
    
    # Sign the message with ed25519 private key
    signing_key = SigningKey(orderly_private_key)
    message_bytes = message.encode("utf-8")
    signature = signing_key.sign(message_bytes).signature
    
    # Encode signature to base64
    signature_base64 = base64.b64encode(signature).decode("utf-8")
    
    # Create headers
    headers = {
        "Content-Type": get_content_type(method),
        "orderly-timestamp": timestamp,
        "orderly-account-id": account_id,
        "orderly-key": orderly_key,
        "orderly-signature": signature_base64,
    }
    
    return {
        "method": method,
        "headers": headers,
        "body": json.dumps(body) if body else None,
    }

