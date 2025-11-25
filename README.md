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

   **Note:** The Orderly account ID is automatically derived from your wallet address and broker ID, so you don't need to set it manually.

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

## Deposit USDC to Orderly

Deposit USDC from your Privy agentic wallet to Orderly Network. The script follows the [Orderly deposit flow](https://orderly.network/docs/build-on-omnichain/user-flows/withdrawal-deposit):

```bash
npm run deposit-usdc -- --wallet-id <wallet_id> --amount <amount>
```

**Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)
- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--amount <amount>`: Amount of USDC to deposit (required, e.g., "100")
- `--chain-id <id>`: Chain ID (optional, default: 80001 = Polygon Mumbai)

**Examples:**

```bash
# Deposit 100 USDC on Polygon Mumbai
npm run deposit-usdc -- --wallet-id wal_xxx --amount 100

# Deposit with specific chain
npm run deposit-usdc -- --wallet-id wal_xxx --amount 50 --chain-id 421614
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Checks USDC balance to ensure sufficient funds
3. Approves USDC transfer to Orderly Vault (if needed)
4. Calculates deposit fee using the Vault contract
5. Generates Orderly account ID from wallet address and broker ID
6. Prepares deposit data with account ID, broker hash, token hash, and amount
7. Calls the deposit function on Orderly Vault contract using Privy signing
8. Waits for transaction confirmation

**Supported Chains:**

- Polygon Mumbai: 80001 (testnet, default)
- Arbitrum Sepolia: 421614 (testnet)
- Ethereum Sepolia: 11155111 (testnet)
- Base Sepolia: 84532 (testnet)
- And other chains supported by Orderly (check their documentation)

**Important Notes:**

- Make sure your wallet has sufficient USDC balance before depositing
- The script automatically approves USDC transfer if needed
- Deposit fee (in native token, e.g., MATIC, ETH) will be included in the transaction
- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- Make sure your wallet has native token (MATIC, ETH, etc.) to pay for gas and deposit fee

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Preparing USDC deposit to Orderly...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Amount: 100 USDC
   Chain ID: 80001 (0x13881)
   Broker ID: woofi_pro
   USDC Address: 0x41e94eb019c0762f9bfcf9fb1f3f082b1e1e2079
   Orderly Vault: 0x816f722424b49cf1275cc86da9840fbd5a6167e9
   USDC decimals: 6
   Amount in smallest unit: 100000000
   Current USDC balance: 150.5
   Current allowance: 0

Approving USDC transfer to Orderly Vault...
   Approval transaction hash: 0x1234567890abcdef...
   Waiting for approval confirmation...
   Approval confirmed in block: 12345
   Allowance verified

Deposit data prepared:
   Account ID: 0xabc123def456...
   Broker Hash: 0x789def...
   Token Hash: 0x456abc...
   Token Amount: 100000000

Calculating deposit fee...
   Deposit fee: 0.001 ETH

Depositing 100 USDC to Orderly Vault...
   Transaction hash: 0x9876543210fedcba...
   Waiting for transaction confirmation...
   Transaction confirmed in block: 12346

✅ USDC deposit successful!

📝 Deposit Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Transaction Hash: 0x9876543210fedcba...
   Block Number: 12346
   Amount: 100 USDC
   Vault Address: 0x816f722424b49cf1275cc86da9840fbd5a6167e9
   Orderly Account ID: 0xabc123def456...
```

## Withdraw USDC from Orderly

Withdraw USDC from your Orderly account to your Privy agentic wallet. The script follows the [Orderly withdrawal flow](https://orderly.network/docs/build-on-omnichain/user-flows/withdrawal-deposit):

```bash
npm run withdraw-usdc -- --wallet-id <wallet_id> --amount <amount>
```

**Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)
- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--amount <amount>`: Amount of USDC to withdraw (required, e.g., "100", minimum: 1.001)
- `--token <token>`: Token symbol to withdraw (optional, default: "USDC")
- `--chain-id <id>`: Chain ID (optional, default: 80001 = Polygon Mumbai)

**Examples:**

```bash
# Withdraw 100 USDC on Polygon Mumbai
npm run withdraw-usdc -- --wallet-id wal_xxx --amount 100

# Withdraw with specific chain
npm run withdraw-usdc -- --wallet-id wal_xxx --amount 50 --chain-id 421614
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Derives Orderly account ID from wallet address and broker ID using the formula: `keccak256(abi.encode(address, keccak256(abi.encodePacked(brokerId))))`
3. Gets withdrawal nonce from Orderly API (`/v1/withdraw_nonce`) using Orderly authentication
4. Converts withdrawal amount to smallest unit based on token decimals
5. Creates EIP-712 typed data message with:
   - `brokerId`: The broker ID (default: "woofi_pro")
   - `chainId`: The chain ID for withdrawal
   - `receiver`: Your wallet address
   - `token`: Token symbol (e.g., "USDC")
   - `amount`: Amount in smallest unit (uint256)
   - `withdrawNonce`: Nonce from step 3 (uint64)
   - `timestamp`: Current timestamp in milliseconds (uint64)
6. Signs the EIP-712 message using Privy's `signTypedData` with authorization context
7. Creates withdrawal request with Orderly API (`/v1/withdraw_request`) using Orderly authentication
8. Returns withdrawal confirmation

**Supported Chains:**

- Polygon Mumbai: 80001 (testnet, default)
- Arbitrum Sepolia: 421614 (testnet)
- Ethereum Sepolia: 11155111 (testnet)
- Base Sepolia: 84532 (testnet)
- And other chains supported by Orderly (check their documentation)

**Important Notes:**

- Make sure your Orderly account has sufficient balance before withdrawing
- Minimum withdrawal amount is 1.001 tokens
- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- Make sure you have added an Orderly key (use `add-orderly-key`)
- The withdrawal will be processed by Orderly Network asynchronously
- Check your wallet on the target chain after processing completes
- Requires `ORDERLY_KEY` and `ORDERLY_PRIVATE_KEY` for API authentication
- Orderly account ID is automatically derived from wallet address and broker ID

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Preparing withdrawal from Orderly...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Amount: 100 USDC
   Chain ID: 80001 (0x13881)
   Broker ID: woofi_pro
   Account ID: 0xabc123def456...

Step 1: Fetching withdrawal nonce...
   Withdrawal nonce: 194528949540

Step 2: Converting amount...
   Token: USDC, Decimals: 6
   Amount: 100 USDC = 100000000 (smallest unit)

Step 3: Creating EIP-712 message...
Message: {
  "brokerId": "woofi_pro",
  "chainId": 80001,
  "receiver": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "token": "USDC",
  "amount": "100000000",
  "withdrawNonce": "194528949540",
  "timestamp": "1685973017064"
}

Step 4: Signing EIP-712 message...
✅ Signature generated: 0x1234567890abcdef...

Step 5: Creating withdrawal request...
Request body: {
  "message": {
    "brokerId": "woofi_pro",
    "chainId": 80001,
    "receiver": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "token": "USDC",
    "amount": "100000000",
    "withdrawNonce": "194528949540",
    "timestamp": "1685973017064"
  },
  "signature": "0x1234567890abcdef...",
  "userAddress": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "verifyingContract": "0x6F7a338F2aA472838dEFD3283eB360d4Dff5D203"
}

✅ Withdrawal request successful!
Response: {
  "success": true,
  "data": {
    "withdraw_id": "0x9876543210fedcba..."
  }
}

📝 Withdrawal Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Amount: 100 USDC
   Target Chain ID: 80001
   Withdrawal Nonce: 194528949540

Note: The withdrawal will be processed by Orderly Network.
Check your wallet on the target chain after processing completes.
```

## Get Current Holding

Get the current summary of token holdings from your Orderly account. The script follows the [Orderly get current holding API](https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-current-holding):

```bash
npm run get-holding -- --wallet-id <wallet_id>
```

**Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)
- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--all`: Include all tokens even if balance is empty (optional, default: false)

**Examples:**

```bash
# Get current holding for a Privy wallet
npm run get-holding -- --wallet-id wal_xxx

# Get holding with wallet address provided
npm run get-holding -- --wallet-id wal_xxx --wallet-address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# Get all tokens including those with zero balance
npm run get-holding -- --wallet-id wal_xxx --all
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Derives Orderly account ID from wallet address and broker ID using the formula: `keccak256(abi.encode(address, keccak256(abi.encodePacked(brokerId))))`
3. Creates authenticated request to Orderly API using Orderly key authentication
4. Calls Orderly API (`GET /v1/client/holding`) to retrieve current holdings
5. Displays formatted holdings information including:
   - Total holding per token
   - Frozen amount
   - Available balance
   - Pending short positions
   - Last update timestamp

**Important Notes:**

- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- Make sure you have added an Orderly key (use `add-orderly-key`)
- Requires `ORDERLY_KEY` and `ORDERLY_PRIVATE_KEY` for API authentication
- Orderly account ID is automatically derived from wallet address and broker ID
- The API has a rate limit of 10 requests per 1 second

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Fetching current holding from Orderly...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Broker ID: woofi_pro
   Account ID: 0xabc123def456...
   Include all tokens: false

✅ Holding retrieved successfully!

📊 Current Holdings:
================================================================================

1. USDT:
   Total Holding: 282,485.071904
   Frozen: 0
   Available: 282,485.071904
   Pending Short: -2,000
   Updated: 1/2/2020, 12:09:09 AM

2. USDC:
   Total Holding: 150,000
   Frozen: 0
   Available: 150,000
   Pending Short: 0
   Updated: 1/2/2020, 12:10:00 AM

================================================================================
Total Holdings: 432,485.071904 (across all tokens)

📝 Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Number of Tokens: 2
   Timestamp: 12/19/2023, 10:33:23 AM
```

## Create Order

Create trading orders on Orderly Network using your Privy agentic wallet. The script follows the [Orderly create order API](https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/create-order):

```bash
npm run create-order -- --wallet-id <wallet_id> --symbol <symbol> --order-type <type> --side <side>
```

**Required Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)
- `--symbol <symbol>`: Trading symbol (e.g., "PERP_ETH_USDC") (required)
- `--order-type <type>`: Order type: LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID (required)
- `--side <side>`: Order side: BUY or SELL (required)

**Optional Options:**

- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--order-price <price>`: Order price (required for LIMIT/IOC/FOK/POST_ONLY)
- `--order-quantity <qty>`: Order quantity in base currency
- `--order-amount <amount>`: Order amount in quote currency (for MARKET/BID/ASK BUY orders)
- `--visible-quantity <qty>`: Visible quantity on orderbook (default: order_quantity)
- `--reduce-only`: Reduce only flag (default: false)
- `--slippage <slippage>`: Slippage tolerance for MARKET orders
- `--client-order-id <id>`: Custom client order ID (36 chars max, unique)
- `--order-tag <tag>`: Order tag
- `--level <level>`: Level for BID/ASK orders (0-4)
- `--post-only-adjust`: Price adjustment for POST_ONLY orders

**Examples:**

```bash
# LIMIT BUY order
npm run create-order -- --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type LIMIT --side BUY --order-price 2000 --order-quantity 0.1

# MARKET BUY order (using orderAmount)
npm run create-order -- --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type MARKET --side BUY --order-amount 100

# LIMIT SELL order
npm run create-order -- --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type LIMIT --side SELL --order-price 2100 --order-quantity 0.05

# LIMIT BUY order with reduce-only
npm run create-order -- --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type LIMIT --side BUY --order-price 2000 --order-quantity 0.1 --reduce-only
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Derives Orderly account ID from wallet address and broker ID using the formula: `keccak256(abi.encode(address, keccak256(abi.encodePacked(brokerId))))`
3. Validates order parameters (order type, side, price requirements, etc.)
4. Builds order request body with all specified parameters
5. Creates authenticated request to Orderly API using Orderly key authentication
6. Calls Orderly API (`POST /v1/order`) to create the order
7. Returns order creation confirmation with order ID

**Order Types:**

- **LIMIT**: Limit order with specified price (requires `--order-price`)
- **MARKET**: Market order executed at current market price
- **IOC**: Immediate or Cancel order (requires `--order-price`)
- **FOK**: Fill or Kill order (requires `--order-price`)
- **POST_ONLY**: Post-only order (requires `--order-price`)
- **ASK**: Ask order for market making
- **BID**: Bid order for market making

**Important Notes:**

- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- Make sure you have added an Orderly key (use `add-orderly-key`)
- Requires `ORDERLY_KEY` and `ORDERLY_PRIVATE_KEY` for API authentication
- Orderly account ID is automatically derived from wallet address and broker ID
- For LIMIT/IOC/FOK/POST_ONLY orders, `--order-price` is required
- For MARKET/BID/ASK BUY orders, use `--order-amount` (not `--order-quantity`)
- For MARKET/BID/ASK SELL orders, use `--order-quantity` (not `--order-amount`)
- Either `--order-quantity` or `--order-amount` must be provided

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Preparing order creation...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Symbol: PERP_ETH_USDC
   Order Type: LIMIT
   Side: BUY

Order parameters: {
  "symbol": "PERP_ETH_USDC",
  "order_type": "LIMIT",
  "side": "BUY",
  "order_price": 2000,
  "order_quantity": 0.1
}

✅ Order created successfully!
Response: {
  "success": true,
  "data": {
    "order_id": 123456789,
    "client_order_id": "custom-id-123",
    "symbol": "PERP_ETH_USDC",
    "order_type": "LIMIT",
    "side": "BUY",
    "order_price": 2000,
    "order_quantity": 0.1,
    "status": "NEW"
  }
}

📝 Order Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Order ID: 123456789
   Client Order ID: custom-id-123
```

## Get Orders

Get orders from your Orderly account with customizable filters. The script follows the [Orderly get orders API](https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-orders):

```bash
npm run get-orders -- --wallet-id <wallet_id>
```

**Required Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)

**Optional Options:**

- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--symbol <symbol>`: Trading symbol filter (e.g., "PERP_ETH_USDC")
- `--side <side>`: Order side filter: BUY or SELL
- `--order-type <type>`: Order type filter: LIMIT or MARKET
- `--status <status>`: Order status filter: NEW, CANCELLED, PARTIAL_FILLED, FILLED, REJECTED, INCOMPLETE, COMPLETED
- `--order-tag <tag>`: Order tag filter
- `--start-time <timestamp>`: Start time range (13-digit timestamp in milliseconds)
- `--end-time <timestamp>`: End time range (13-digit timestamp in milliseconds)
- `--page <page>`: Page number (starts from 1, default: 1)
- `--size <size>`: Page size (max: 500, default: 25)
- `--sort-by <sort>`: Sort by: CREATED_TIME_DESC, CREATED_TIME_ASC, UPDATED_TIME_DESC, UPDATED_TIME_ASC

**Status Values:**

- `NEW`: New orders
- `CANCELLED`: Cancelled orders
- `PARTIAL_FILLED`: Partially filled orders
- `FILLED`: Fully filled orders
- `REJECTED`: Rejected orders
- `INCOMPLETE`: NEW + PARTIAL_FILLED (bundled status)
- `COMPLETED`: CANCELLED + FILLED (bundled status)

**Examples:**

```bash
# Get all orders for a Privy wallet
npm run get-orders -- --wallet-id wal_xxx

# Get orders for a specific symbol
npm run get-orders -- --wallet-id wal_xxx --symbol "PERP_ETH_USDC"

# Get only BUY orders
npm run get-orders -- --wallet-id wal_xxx --side BUY

# Get incomplete orders (NEW + PARTIAL_FILLED)
npm run get-orders -- --wallet-id wal_xxx --status INCOMPLETE

# Get orders with pagination
npm run get-orders -- --wallet-id wal_xxx --page 1 --size 50

# Get orders sorted by creation time (descending)
npm run get-orders -- --wallet-id wal_xxx --sort-by CREATED_TIME_DESC

# Get orders within a time range
npm run get-orders -- --wallet-id wal_xxx --start-time 1653563963000 --end-time 1653564213000
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Derives Orderly account ID from wallet address and broker ID using the formula: `keccak256(abi.encode(address, keccak256(abi.encodePacked(brokerId))))`
3. Builds query parameters from provided filters
4. Creates authenticated request to Orderly API using Orderly key authentication
5. Calls Orderly API (`GET /v1/orders`) to retrieve orders
6. Displays formatted orders information including:
   - Order ID, symbol, side, type, status
   - Price, quantity, executed quantity
   - Fees, realized PnL
   - Creation and update timestamps
   - Pagination metadata

**Important Notes:**

- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- Make sure you have added an Orderly key (use `add-orderly-key`)
- Requires `ORDERLY_KEY` and `ORDERLY_PRIVATE_KEY` for API authentication
- Orderly account ID is automatically derived from wallet address and broker ID
- The API has a rate limit of 10 requests per 1 second
- Maximum page size is 500
- Default sorting: descending by created_time (or updated_time if time filters are used)

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Fetching orders from Orderly...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Filters: symbol=PERP_ETH_USDC&status=INCOMPLETE

✅ Orders retrieved successfully!

📋 Orders:
====================================================================================================

Total Orders: 9
Page: 1 of 1
Records per page: 25

1. Order #78151:
   Symbol: PERP_WOO_USDC
   Side: BUY
   Type: LIMIT
   Status: FILLED
   Price: 0.67772
   Quantity: 20
   Amount: 10
   Executed Quantity: 20
   Total Executed Quantity: 20
   Visible Quantity: 1
   Average Executed Price: 0.67772
   Total Fee: 0.5 WOO
   Client Order ID: 1
   Realized PnL: 0
   Created: 5/25/2022, 10:39:23 AM
   Updated: 5/25/2022, 10:43:33 AM

2. Order #78152:
   Symbol: PERP_ETH_USDC
   Side: SELL
   Type: LIMIT
   Status: NEW
   Price: 2100
   Quantity: 0.5
   Executed Quantity: 0
   Total Executed Quantity: 0
   Visible Quantity: 0.5
   Average Executed Price: 0
   Total Fee: 0 USDC
   Realized PnL: 0
   Created: 5/25/2022, 11:00:00 AM
   Updated: 5/25/2022, 11:00:00 AM

====================================================================================================

📝 Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Number of Orders: 2
   Total Orders: 9
   Timestamp: 12/19/2023, 10:33:23 AM
```

## Cancel Order

Cancel an order on Orderly Network by order ID. The script follows the [Orderly cancel order API](https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/cancel-order):

```bash
npm run cancel-order -- --wallet-id <wallet_id> --order-id <order_id> --symbol <symbol>
```

**Required Options:**

- `--wallet-id <id>`: Privy wallet ID to use (required)
- `--order-id <id>`: Order ID to cancel (required)
- `--symbol <symbol>`: Trading symbol (e.g., "PERP_ETH_USDC") (required)

**Optional Options:**

- `--wallet-address <addr>`: Wallet address (optional, will be fetched if not provided)
- `--help, -h`: Show this help message

**Examples:**

```bash
# Cancel order by order ID
npm run cancel-order -- --wallet-id wal_xxx --order-id 12345 --symbol "PERP_ETH_USDC"

# Cancel order with wallet address provided
npm run cancel-order -- --wallet-id wal_xxx --wallet-address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --order-id 12345 --symbol "PERP_ETH_USDC"
```

**How it works:**

1. Fetches your wallet address from Privy (if not provided)
2. Derives Orderly account ID from wallet address and broker ID using the formula: `keccak256(abi.encode(address, keccak256(abi.encodePacked(brokerId))))`
3. Validates required parameters (order ID and symbol)
4. Builds query parameters with order ID and symbol
5. Creates authenticated request to Orderly API using Orderly key authentication
6. Calls Orderly API (`DELETE /v1/order`) to cancel the order
7. Returns cancellation confirmation with order status

**Important Notes:**

- Make sure your wallet has been registered with Orderly first (use `register-orderly`)
- Make sure you have added an Orderly key (use `add-orderly-key`)
- Requires `ORDERLY_KEY` and `ORDERLY_PRIVATE_KEY` for API authentication
- Orderly account ID is automatically derived from wallet address and broker ID
- Both order ID and symbol are required to cancel an order
- Only orders that are in NEW or PARTIAL_FILLED status can be cancelled

**Sample Output:**

```
Fetching wallet details...
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

Preparing order cancellation...
   Wallet ID: wal_abc123xyz
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Order ID: 12345
   Symbol: PERP_ETH_USDC

✅ Order cancelled successfully!
Response: {
  "success": true,
  "data": {
    "status": "CANCELLED",
    "order_id": 12345,
    "symbol": "PERP_ETH_USDC"
  }
}

📝 Cancellation Summary:
   Wallet Address: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
   Account ID: 0xabc123def456...
   Order ID: 12345
   Symbol: PERP_ETH_USDC
   Status: CANCELLED
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

### depositUSDC.js

- Deposits USDC from Privy agentic wallets to Orderly Network
- Uses Privy's sendTransaction for contract interactions
- Automatically approves USDC transfer if needed
- Calculates and includes deposit fee
- Generates Orderly account ID from wallet address and broker ID
- Validates balance before depositing
- Supports multiple chains with pre-configured USDC and Vault addresses
- Uses authorization context for secure transaction signing

### withdrawUSDC.js

- Withdraws USDC from Orderly account to Privy agentic wallets
- Uses Privy's signTypedData for EIP-712 message signing
- Uses Orderly API authentication for authenticated requests
- Gets withdrawal nonce from Orderly API
- Creates and signs EIP-712 typed data messages using Privy
- Uses authorization context for secure signing
- Supports multiple chains and tokens
- Follows Orderly's withdrawal flow

### getHolding.js

- Gets current token holdings from Orderly account
- Uses Orderly API authentication for authenticated requests
- Derives Orderly account ID from wallet address and broker ID
- Supports optional `--all` flag to include tokens with zero balance
- Formats and displays holdings information in a readable format
- Shows total holding, frozen amount, available balance, and pending short positions

### createOrder.js

- Creates trading orders on Orderly Network using Privy agentic wallets
- Uses Orderly API authentication for authenticated requests
- Derives Orderly account ID from wallet address and broker ID
- Supports all order types: LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID
- Validates order parameters and requirements
- Supports optional parameters like reduce-only, slippage, client order ID, etc.
- Follows Orderly's order creation API

### getOrders.js

- Gets orders from Orderly account with customizable filters
- Uses Orderly API authentication for authenticated requests
- Derives Orderly account ID from wallet address and broker ID
- Supports filtering by symbol, side, order type, status, order tag, and time range
- Supports pagination with configurable page size (max: 500)
- Supports sorting by creation time or update time (ascending/descending)
- Formats and displays orders information in a readable format
- Shows order details including execution status, fees, and PnL
- Follows Orderly's get orders API

### cancelOrder.js

- Cancels orders on Orderly Network by order ID
- Uses Orderly API authentication for authenticated requests
- Derives Orderly account ID from wallet address and broker ID
- Validates required parameters (order ID and symbol)
- Uses DELETE method to cancel orders via Orderly API
- Returns cancellation confirmation with order status
- Follows Orderly's cancel order API

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
