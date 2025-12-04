"""
Database module for storing Orderly keys per wallet_id
Uses PostgreSQL for Heroku deployment (DATABASE_URL env var required)
"""
import os
from typing import Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor


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
    
    Args:
        wallet_id: The Privy wallet ID
        orderly_key: The Orderly public key (ed25519:...)
        orderly_private_key_hex: The Orderly private key in hex format
    """
    init_db()  # Ensure table exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO privy_orderly_account_private_keys 
            (wallet_id, orderly_key, orderly_private_key_hex, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (wallet_id) 
            DO UPDATE SET 
                orderly_key = EXCLUDED.orderly_key,
                orderly_private_key_hex = EXCLUDED.orderly_private_key_hex,
                updated_at = CURRENT_TIMESTAMP
        """, (wallet_id, orderly_key, orderly_private_key_hex))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_orderly_keys(wallet_id: str) -> Optional[Tuple[str, str]]:
    """
    Get Orderly keys for a wallet
    
    Args:
        wallet_id: The Privy wallet ID
        
    Returns:
        Tuple of (orderly_key, orderly_private_key_hex) or None if not found
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
            return (row["orderly_key"], row["orderly_private_key_hex"])
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

