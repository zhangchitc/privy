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

**Important Notes:**
- The script uses your `PRIVY_AUTHORIZATION_SECRET` to sign the transaction
- Make sure your wallet has testnet ETH before sending transactions
- Use testnets for demos/testing - mainnet transactions cost real money!

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
- [Ethereum Testnets Guide](https://ethereum.org/en/developers/docs/networks/#ethereum-testnets)

