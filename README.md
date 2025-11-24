# Privy Agentic Wallet Creator

A backend script to create Agentic wallets using Privy's API.

## Prerequisites

- Node.js installed
- A Privy account with an App ID and App Secret
- Authorization keys created in the Privy Dashboard

## Setup

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Create a `.env` file** in the root directory with the following variables:

   ```env
   PRIVY_APP_ID=your_app_id_here
   PRIVY_APP_SECRET=your_app_secret_here
   PRIVY_AUTHORIZATION_ID=your_authorization_id_here
   PRIVY_AUTHORIZATION_SECRET=your_authorization_secret_here
   ```

   **Note:** After running `add-orderly-key`, the following will be automatically added to your `.env` file:

   ```env
   ORDERLY_KEY=ed25519:...
   ORDERLY_PRIVATE_KEY=...
   ```

3. **Get your credentials from Privy Dashboard:**
   - **App ID & App Secret**: Found in your Privy Dashboard under App Settings
   - **Authorization ID & Secret**:
     - Go to [Authorization Keys](https://dashboard.privy.io/authorization-keys) in your Privy Dashboard
     - Create a new authorization key if you haven't already
     - Copy the Authorization ID and Secret

## Usage

### Basic Usage

Create a simple agentic wallet:

```bash
npm run create-wallet
```

**Sample Output:**

```
Creating agentic wallet...
Wallet configuration: {
  "chain_type": "ethereum",
  "owner_id": "auth_key_abc123"
}

✅ Agentic wallet created successfully!
Wallet details: {
  "id": "wal_xyz789",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "chain_type": "ethereum",
  "owner_id": "auth_key_abc123",
  "policy_ids": [],
  "created_at": 1685973017064
}

📝 Wallet Summary:
   Wallet ID: wal_xyz789
   Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Owner ID: auth_key_abc123
   Chain Type: ethereum
```

### With Options

Create a wallet with a policy and custom name:

```bash
npm run create-wallet -- --policy-id <policy_id> --name "My Agent Wallet"
```

### Available Options

- `--policy-id <id>`: Assign a policy ID to the wallet (optional)
- `--name <name>`: Set a custom name for the wallet (optional)
- `--chain-type <type>`: Specify chain type ('ethereum' or 'solana'), defaults to 'ethereum' (optional)

### Examples

```bash
# Create an Ethereum wallet with a policy
npm run create-wallet -- --policy-id pol_abc123 --name "Trading Bot Wallet"

# Create a Solana wallet
npm run create-wallet -- --chain-type solana --name "Solana Agent"

# Create a wallet with multiple options
npm run create-wallet -- --policy-id pol_abc123 --name "My Agent" --chain-type ethereum
```

## Sending Transactions

### Testnet Recommendations

**For demo/testing purposes, use testnets to avoid high costs:**

1. **Sepolia Testnet (Recommended)** - Chain ID: `11155111`

   - Most stable and widely supported Ethereum testnet
   - Get testnet ETH from: [Sepolia Faucet](https://sepoliafaucet.com/) or [Alchemy Sepolia Faucet](https://sepoliafaucet.com/)

2. **Base Sepolia** - Chain ID: `84532`

   - Lower gas costs, faster transactions
   - Get testnet ETH from: [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)

3. **Polygon Mumbai** - Chain ID: `80001`
   - Very low gas costs
   - Get testnet MATIC from: [Polygon Faucet](https://faucet.polygon.technology/)

### Send Transaction

Send a transaction from your agentic wallet:

```bash
npm run send-transaction -- --wallet-id <wallet_id> --to <recipient_address>
```

**Options:**

- `--wallet-id <id>`: Wallet ID to send from (required)
- `--to <address>`: Recipient Ethereum address (required)
- `--value <wei>`: Amount in wei (optional, default: 0.001 ETH)
- `--chain-id <id>`: Chain ID (optional, default: 11155111 = Sepolia)

**Examples:**

```bash
# Send 0.001 ETH on Sepolia testnet
npm run send-transaction -- --wallet-id wal_xxx --to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# Send custom amount on Base Sepolia
npm run send-transaction -- --wallet-id wal_xxx --to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --value 2000000000000000 --chain-id 84532
```

**Sample Output:**

```
Preparing transaction...
   Wallet ID: wal_xyz789
   To: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Value: 1000000000000000 wei (0.001 ETH) = 0x38d7ea4c68000
   Chain ID: 11155111 (Sepolia Testnet) = 0xaa36a7

✅ Transaction sent successfully!
Transaction details: {
  "transaction_hash": "0x1234567890abcdef...",
  "status": "pending",
  "block_number": null
}

📝 Transaction Summary:
   Transaction Hash: 0x1234567890abcdef...
   Status: pending
```

**Important Notes:**

- The script uses your `PRIVY_AUTHORIZATION_SECRET` to sign the transaction
- Make sure your wallet has testnet ETH before sending transactions
- Use testnets for demos/testing - mainnet transactions cost real money!

## Register Orderly Account

Register your agentic wallet with Orderly Network for trading. The script follows the [Orderly account registration flow](https://orderly.network/docs/build-on-omnichain/user-flows/accounts):

```bash
npm run register-orderly -- --wallet-id <wallet_id>
```

**Options:**

- `--wallet-id <id>`: Wallet ID to use for registration (required)
- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--chain-id <id>`: Chain ID (optional, default: 421614 = Arbitrum Sepolia)

**Examples:**

```bash
# Register account on Orderly
npm run register-orderly -- --wallet-id wal_xxx

# Register with specific chain
npm run register-orderly -- --wallet-id wal_xxx --chain-id 421614
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Gets a registration nonce from Orderly API (`/v1/registration_nonce`)
3. Creates an EIP-712 typed data message with:
   - `brokerId`: The builder/broker ID (default: "woofi_pro")
   - `chainId`: The chain ID for registration
   - `timestamp`: Current timestamp in milliseconds
   - `registrationNonce`: Nonce from step 2
4. Signs the EIP-712 message using your authorization secret
5. Registers the account with Orderly API (`/v1/register_account`)

**Supported Chains:**

- Arbitrum Sepolia: 421614 (testnet, recommended for testing)
- Arbitrum One: 42161 (mainnet)
- Other chains supported by Orderly (check their documentation)

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Preparing Orderly account registration...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Chain ID: 421614 (0x66eee)
   Broker ID: woofi_pro
   Orderly API: https://api.orderly.org

Step 1: Getting registration nonce...
   Registration Nonce: 194528949540

Step 2: Signing EIP-712 message...
Register message: {
  "brokerId": "woofi_pro",
  "chainId": 421614,
  "timestamp": 1685973017064,
  "registrationNonce": "194528949540"
}

✅ Signature generated: 0x1234567890abcdef...

Step 3: Registering account with Orderly...
Registration payload: {
  "message": {
    "brokerId": "woofi_pro",
    "chainId": 421614,
    "timestamp": 1685973017064,
    "registrationNonce": "194528949540"
  },
  "signature": "0x1234567890abcdef...",
  "userAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}

✅ Account registered successfully with Orderly!
Registration response: {
  "success": true,
  "data": {
    "account_id": "0xabc123def456..."
  }
}

📝 Orderly Account ID: 0xabc123def456...

📝 Registration Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Orderly Account ID: 0xabc123def456...
```

## Add Orderly Key

Add an Orderly authentication key for your Privy wallet. This generates an ed25519 key pair for Orderly API authentication. The script follows the [Orderly wallet authentication flow](https://orderly.network/docs/build-on-omnichain/user-flows/wallet-authentication):

```bash
npm run add-orderly-key -- --wallet-id <wallet_id>
```

**Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)
- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--chain-id <id>`: Chain ID (optional, default: 80001 = Polygon Mumbai)

**Examples:**

```bash
# Add Orderly Key for a Privy wallet
npm run add-orderly-key -- --wallet-id wal_xxx

# Add Orderly Key with specific chain
npm run add-orderly-key -- --wallet-id wal_xxx --chain-id 80001
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Generates an ed25519 key pair for Orderly authentication
3. Creates an EIP-712 typed data message with:
   - `brokerId`: The broker ID (default: "woofi_pro")
   - `chainId`: The chain ID
   - `orderlyKey`: The generated ed25519 public key
   - `scope`: Permission scope (default: "read,trading")
   - `timestamp`: Current timestamp in milliseconds
   - `expiration`: Expiration timestamp (default: 365 days)
4. Signs the EIP-712 message using your authorization secret
5. Adds the Orderly Key via Orderly API (`/v1/orderly_key`)
6. Saves the Orderly Key and Private Key to your `.env` file

**Important Notes:**

- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- The generated keys are automatically saved to your `.env` file
- The Orderly Key can be used for API authentication with Orderly
- Keep your `ORDERLY_PRIVATE_KEY` secure - it's used to sign API requests

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Adding Orderly Key for Privy wallet...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Chain ID: 80001 (0x13881)
   Broker ID: woofi_pro

Generating ed25519 key pair...
   Generated Orderly Key: ed25519:AbCdEf123456...
   Generated Orderly Private Key: 0123456789abcdef...

Signing EIP-712 message...
Message: {
  "brokerId": "woofi_pro",
  "chainId": 80001,
  "orderlyKey": "ed25519:AbCdEf123456...",
  "scope": "read,trading",
  "timestamp": 1685973017064,
  "expiration": 1717509017064
}

✅ Signature generated: 0x1234567890abcdef...

Adding Orderly Key to Orderly...

✅ Orderly Key added successfully!
Response: {
  "success": true,
  "data": {
    "orderly_key": "ed25519:AbCdEf123456..."
  }
}

✅ Saved to .env file:
   ORDERLY_KEY=ed25519:AbCdEf123456...
   ORDERLY_PRIVATE_KEY=0123456789abcdef...

📝 Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Orderly Key: ed25519:AbCdEf123456...
   Orderly Private Key: 0123456789abcdef...
```

## Script Details

### createAgenticWallet.js

- Loads environment variables from `.env`
- Validates required credentials
- Initializes the Privy client
- Creates an agentic wallet owned by your authorization key
- Optionally assigns policies to the wallet
- Returns wallet details including ID, address, and owner information

### sendTransaction.js

- Sends transactions from agentic wallets
- Uses authorization context with your authorization secret
- Supports testnet configurations (Sepolia, Base Sepolia, Polygon Mumbai)
- Validates wallet balance and transaction parameters

### registerOrderlyAccount.js

- Registers agentic wallets with Orderly Network following the official registration flow
- Gets registration nonce from Orderly API
- Creates and signs EIP-712 typed data messages using Privy
- Uses authorization context for secure signing
- Supports multiple chains (Arbitrum Sepolia, Arbitrum One, etc.)
- Automatically fetches wallet address if not provided
- Returns Orderly account ID upon successful registration

### addOrderlyKey.js

- Adds Orderly authentication keys for Privy wallets
- Generates ed25519 key pairs for Orderly API authentication
- Creates and signs EIP-712 typed data messages using Privy
- Uses authorization context for secure signing
- Automatically saves generated keys to `.env` file
- Supports custom chain IDs
- Follows Orderly's wallet authentication flow

## Error Handling

The scripts will:

- Validate that all required environment variables are set
- Display clear error messages if operations fail
- Show detailed error information from the Privy API

## Security Notes

- **Never commit your `.env` file** to version control
- Keep your App Secret and Authorization Secret secure
- Use environment variables or secure secret management in production
- Consider using a key quorum for enhanced security with multiple authorization keys

## Testnet Faucets

Get free testnet tokens for testing:

- **Sepolia ETH**: [sepoliafaucet.com](https://sepoliafaucet.com/) | [Alchemy Faucet](https://sepoliafaucet.com/)
- **Base Sepolia ETH**: [Base Faucet](https://www.coinbase.com/faucets/base-ethereum-goerli-faucet)
- **Polygon Mumbai MATIC**: [Polygon Faucet](https://faucet.polygon.technology/)

## Additional Resources

- [Privy Agentic Wallets Documentation](https://docs.privy.io/recipes/wallets/agentic-wallets)
- [Privy API Reference](https://docs.privy.io/api-reference/wallets/create)
- [Privy Dashboard](https://dashboard.privy.io)
- [Orderly Network Documentation](https://orderly.network/docs)
- [Orderly Account Registration Flow](https://orderly.network/docs/build-on-omnichain/user-flows/accounts)
- [Orderly Wallet Authentication Flow](https://orderly.network/docs/build-on-omnichain/user-flows/wallet-authentication)
- [Ethereum Testnets Guide](https://ethereum.org/en/developers/docs/networks/#ethereum-testnets)
