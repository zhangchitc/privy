"""
Database module for storing Orderly keys per wallet_id
Uses SQLite for simplicity - no server required, built into Python
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional, Tuple


# Database file path (in the same directory as this script)
DB_PATH = Path(__file__).parent / "orderly_keys.db"


def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist"""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orderly_keys (
                wallet_id TEXT PRIMARY KEY,
                orderly_key TEXT NOT NULL,
                orderly_private_key_hex TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
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
    try:
        conn.execute("""
            INSERT OR REPLACE INTO orderly_keys 
            (wallet_id, orderly_key, orderly_private_key_hex, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (wallet_id, orderly_key, orderly_private_key_hex))
        conn.commit()
    finally:
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
    try:
        cursor = conn.execute(
            "SELECT orderly_key, orderly_private_key_hex FROM orderly_keys WHERE wallet_id = ?",
            (wallet_id,)
        )
        row = cursor.fetchone()
        if row:
            return (row["orderly_key"], row["orderly_private_key_hex"])
        return None
    finally:
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
    try:
        cursor = conn.execute("DELETE FROM orderly_keys WHERE wallet_id = ?", (wallet_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def list_all_wallets() -> list:
    """
    List all wallet IDs that have Orderly keys stored
    
    Returns:
        List of wallet IDs
    """
    init_db()  # Ensure table exists
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT wallet_id, created_at, updated_at FROM orderly_keys ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

