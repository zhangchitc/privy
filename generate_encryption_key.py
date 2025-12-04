#!/usr/bin/env python3
"""
Generate an encryption key for ENCRYPTION_KEY environment variable
Run this script to generate a secure encryption key for encrypting private keys in the database
"""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("=" * 60)
    print("Generated ENCRYPTION_KEY:")
    print("=" * 60)
    print(key.decode())
    print("=" * 60)
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("\nOr set it as an environment variable:")
    print(f"export ENCRYPTION_KEY={key.decode()}")
    print("\nFor Heroku:")
    print(f"heroku config:set ENCRYPTION_KEY={key.decode()} -a your-app-name")
    print("=" * 60)

