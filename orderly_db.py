"""
Database module for storing Orderly keys per wallet_id
Uses PostgreSQL for Heroku deployment (DATABASE_URL env var required)
Private keys are encrypted at rest using Fernet symmetric encryption
"""
import os
import base64
from typing import Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from environment variable
    
    Returns:
        Fernet encryption key (32 bytes, base64-encoded)
    """
    encryption_key = os.environ.get("ENCRYPTION_KEY")
    
    if not encryption_key:
        raise RuntimeError(
            "ENCRYPTION_KEY environment variable is required. "
            "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # If it's a password, derive a key from it
    # Otherwise, use it directly as a Fernet key
    if len(encryption_key) == 44 and encryption_key.endswith('='):
        # Looks like a Fernet key (base64, 44 chars)
        return encryption_key.encode()
    else:
        # Derive key from password using PBKDF2
        salt = os.environ.get("ENCRYPTION_SALT", "privy_orderly_salt").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        return key


def _get_cipher() -> Fernet:
    """Get Fernet cipher instance for encryption/decryption"""
    key = _get_encryption_key()
    return Fernet(key)


def _encrypt_private_key(private_key_hex: str) -> str:
    """
    Encrypt private key before storing in database
    
    Args:
        private_key_hex: Private key in hex format
        
    Returns:
        Encrypted private key (base64-encoded)
    """
    cipher = _get_cipher()
    encrypted = cipher.encrypt(private_key_hex.encode())
    return encrypted.decode()


def _decrypt_private_key(encrypted_key: str) -> str:
    """
    Decrypt private key after retrieving from database
    Handles both encrypted and plaintext (for backward compatibility)
    
    Args:
        encrypted_key: Encrypted private key or plaintext
        
    Returns:
        Decrypted private key in hex format
    """
    cipher = _get_cipher()
    
    try:
        # Try to decrypt (assumes it's encrypted)
        decrypted = cipher.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception:
        # If decryption fails, assume it's plaintext (backward compatibility)
        # Check if it looks like hex (only contains 0-9, a-f)
        if all(c in '0123456789abcdef' for c in encrypted_key.lower()):
            return encrypted_key
        # If not hex, raise error
        raise ValueError("Failed to decrypt private key and it doesn't appear to be plaintext hex")


def get_db_connection():
    """Get a PostgreSQL database connection"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    
    # Heroku uses postgres:// but psycopg2 requires postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return psycopg2.connect(database_url)


def init_db():
    """Initialize the database and create tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS privy_orderly_account_private_keys (
                wallet_id VARCHAR(255) PRIMARY KEY,
                orderly_key TEXT NOT NULL,
                orderly_private_key_hex TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def save_orderly_keys(wallet_id: str, orderly_key: str, orderly_private_key_hex: str) -> None:
    """
    Save or update Orderly keys for a wallet
    Private key is encrypted before storing in the database
    
    Args:
        wallet_id: The Privy wallet ID
        orderly_key: The Orderly public key (ed25519:...)
        orderly_private_key_hex: The Orderly private key in hex format (will be encrypted)
    """
    init_db()  # Ensure table exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Encrypt the private key before storing
        encrypted_private_key = _encrypt_private_key(orderly_private_key_hex)
        
        cursor.execute("""
            INSERT INTO privy_orderly_account_private_keys 
            (wallet_id, orderly_key, orderly_private_key_hex, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (wallet_id) 
            DO UPDATE SET 
                orderly_key = EXCLUDED.orderly_key,
                orderly_private_key_hex = EXCLUDED.orderly_private_key_hex,
                updated_at = CURRENT_TIMESTAMP
        """, (wallet_id, orderly_key, encrypted_private_key))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_orderly_keys(wallet_id: str) -> Optional[Tuple[str, str]]:
    """
    Get Orderly keys for a wallet
    Private key is decrypted after retrieving from the database
    
    Args:
        wallet_id: The Privy wallet ID
        
    Returns:
        Tuple of (orderly_key, orderly_private_key_hex) or None if not found
        The private key is decrypted before returning
    """
    init_db()  # Ensure table exists
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            "SELECT orderly_key, orderly_private_key_hex FROM privy_orderly_account_private_keys WHERE wallet_id = %s",
            (wallet_id,)
        )
        row = cursor.fetchone()
        if row:
            # Decrypt the private key
            decrypted_private_key = _decrypt_private_key(row["orderly_private_key_hex"])
            return (row["orderly_key"], decrypted_private_key)
        return None
    finally:
        cursor.close()
        conn.close()


def get_orderly_keys_or_raise(wallet_id: str) -> Tuple[str, str]:
    """
    Get Orderly keys for a wallet, raising an error if not found
    
    Args:
        wallet_id: The Privy wallet ID
        
    Returns:
        Tuple of (orderly_key, orderly_private_key_hex)
        
    Raises:
        ValueError: If keys are not found for the wallet
    """
    keys = get_orderly_keys(wallet_id)
    if keys is None:
        raise ValueError(
            f"Orderly keys not found for wallet_id: {wallet_id}. "
            f"Please add Orderly keys first using add_orderly_key.py"
        )
    return keys


def delete_orderly_keys(wallet_id: str) -> bool:
    """
    Delete Orderly keys for a wallet
    
    Args:
        wallet_id: The Privy wallet ID
        
    Returns:
        True if deleted, False if not found
    """
    init_db()  # Ensure table exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM privy_orderly_account_private_keys WHERE wallet_id = %s", (wallet_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def list_all_wallets() -> list:
    """
    List all wallet IDs that have Orderly keys stored
    
    Returns:
        List of wallet IDs
    """
    init_db()  # Ensure table exists
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT wallet_id, created_at, updated_at FROM privy_orderly_account_private_keys ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

