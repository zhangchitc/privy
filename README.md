# Privy Orderly Integration

Python backend for creating and managing Privy agentic wallets with Orderly Network integration. Includes REST API server for trading operations.

## Prerequisites

- **Python 3.8+** installed
- **PostgreSQL database** (for storing Orderly keys, can use local PostgreSQL or cloud service like Heroku Postgres)
- A **Privy account** with an App ID and App Secret
- **Authorization keys** created in the Privy Dashboard

## Setup

1. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database:**

   - **Local PostgreSQL**: Install and create a database
   - **Heroku Postgres**: Add Heroku Postgres addon to your app
   - **Other cloud providers**: Set up a PostgreSQL database and get the connection URL

3. **Create a `.env` file** in the root directory with the following variables:

   ```env
   # Privy Credentials (Required)
   PRIVY_APP_ID=your_app_id_here
   PRIVY_APP_SECRET=your_app_secret_here
   PRIVY_AUTHORIZATION_ID=your_authorization_id_here
   PRIVY_AUTHORIZATION_SECRET=your_authorization_secret_here

   # Database Configuration (Required)
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   # Or for Heroku: postgres://user:password@host:port/dbname

   # Encryption Key (Required for database encryption)
   # Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
   ENCRYPTION_KEY=your_encryption_key_here

   # Optional: Custom encryption salt (defaults to "privy_orderly_salt")
   ENCRYPTION_SALT=privy_orderly_salt

   # API Server Configuration (Optional)
   API_KEY=your_api_key_here  # Optional: Set to enable API key authentication
   PORT=3000                   # Optional: Server port (default: 3000)
   FLASK_DEBUG=False          # Optional: Enable Flask debug mode (default: False)
   ```

   **Note:** After running `add_orderly_key.py`, Orderly keys are automatically saved to the database (encrypted). You don't need to manually set `ORDERLY_KEY` or `ORDERLY_PRIVATE_KEY` in your `.env` file.

   **Note:** The Orderly account ID is automatically derived from your wallet address and broker ID, so you don't need to set it manually.

4. **Get your credentials from Privy Dashboard:**

   - **App ID & App Secret**: Found in your Privy Dashboard under App Settings
   - **Authorization ID & Secret**:
     - Go to [Authorization Keys](https://dashboard.privy.io/authorization-keys) in your Privy Dashboard
     - Create a new authorization key if you haven't already
     - Copy the Authorization ID and Secret

5. **Generate Encryption Key:**

   ```bash
   python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
   ```

   Copy the output and add it to your `.env` file as `ENCRYPTION_KEY`.

## API Server

The project includes a Flask server (`server.py`) that exposes REST API endpoints for all Privy/Orderly operations. This allows you to interact with the system via HTTP requests.

### Running the Server Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env file
# Run the server
python server.py
```

The server will run on `http://localhost:3000` by default (or the port specified by the `PORT` environment variable).

### Base URL

- **Production**: `https://your-api-server.com` (replace with your server URL)
- **Local Development**: `http://localhost:3000`

### Authentication

Most endpoints require API key authentication via the `X-API-Key` header. Set the `API_KEY` environment variable on the server to enable authentication. If no `API_KEY` is set, authentication is skipped (for development only).

### API Endpoints

#### Health Check

Check if the server is running.

```bash
curl -X GET "https://your-api-server.com/api/health"
```

**Response:**

```json
{
  "success": true,
  "message": "Server is running"
}
```

#### Create Wallet

Create a new Privy agentic wallet.

```bash
curl -X POST "https://your-api-server.com/api/create-wallet" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "chainType": "ethereum",
    "policyId": "pol_xxx"
  }'
```

**Request Body:**

- `chainType` (string, optional): Chain type, defaults to "ethereum"
- `policyId` (string, optional): Policy ID to assign to the wallet

#### Register Orderly Account

Register a wallet with Orderly Network.

```bash
curl -X POST "https://your-api-server.com/api/register-orderly" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "chainId": "421614"
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `chainId` (string, optional): Chain ID, defaults to "421614"

#### Add Orderly Key

Add an Orderly authentication key for a wallet.

```bash
curl -X POST "https://your-api-server.com/api/add-orderly-key" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "chainId": 80001
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `chainId` (integer, optional): Chain ID

#### Prepare Orderly Account

Complete wallet setup: creates wallet, registers Orderly account, and adds Orderly key in one call.

```bash
curl -X POST "https://your-api-server.com/api/prepare-orderly-account" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "chainType": "ethereum",
    "chainId": "421614",
    "policyId": "pol_xxx"
  }'
```

**Request Body:**

- `chainType` (string, optional): Chain type, defaults to "ethereum"
- `chainId` (string, optional): Chain ID, defaults to "421614"
- `policyId` (string, optional): Policy ID

#### Deposit USDC

Deposit USDC to Orderly account.

```bash
curl -X POST "https://your-api-server.com/api/deposit-usdc" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "amount": "100",
    "chainId": 80001
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `amount` (string, required): Amount of USDC to deposit
- `chainId` (integer, optional): Chain ID

#### Get Holding

Get current token holdings from Orderly account.

```bash
curl -X POST "https://your-api-server.com/api/get-holding" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx"
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID

#### Get Positions

Get all open positions from Orderly account.

```bash
curl -X POST "https://your-api-server.com/api/get-positions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx"
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID

#### Create Order

Create a trading order on Orderly Network.

```bash
curl -X POST "https://your-api-server.com/api/create-order" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "symbol": "PERP_ETH_USDC",
    "orderType": "MARKET",
    "side": "BUY",
    "orderQuantity": 0.1
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `symbol` (string, required): Trading symbol (e.g., "PERP_ETH_USDC")
- `orderType` (string, required): Order type (LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID)
- `side` (string, required): Order side (BUY or SELL)
- `orderPrice` (float, optional): Order price (required for LIMIT/IOC/FOK/POST_ONLY)
- `orderQuantity` (float, optional): Order quantity in base currency
- `orderAmount` (float, optional): Order amount in quote currency (for MARKET BUY orders on spot)
- `visibleQuantity` (float, optional): Visible quantity on orderbook
- `reduceOnly` (boolean, optional): Reduce only flag
- `slippage` (float, optional): Slippage tolerance for MARKET orders
- `clientOrderId` (string, optional): Custom client order ID
- `orderTag` (string, optional): Order tag
- `level` (integer, optional): Level for BID/ASK orders (0-4)

**Note:** For futures/perpetual contracts (symbols starting with `PERP_`), use `orderQuantity` for both BUY and SELL MARKET orders. `orderAmount` is only supported for spot markets.

#### Get Orders

Get orders from Orderly account with filters.

```bash
curl -X POST "https://your-api-server.com/api/get-orders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "symbol": "PERP_ETH_USDC",
    "status": "NEW",
    "page": 1,
    "size": 25
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `symbol` (string, optional): Trading symbol filter
- `side` (string, optional): Order side filter (BUY or SELL)
- `orderType` (string, optional): Order type filter
- `status` (string, optional): Order status filter
- `orderTag` (string, optional): Order tag filter
- `startTime` (integer, optional): Start time range (timestamp in milliseconds)
- `endTime` (integer, optional): End time range (timestamp in milliseconds)
- `page` (integer, optional): Page number, defaults to 1
- `size` (integer, optional): Page size, defaults to 25, max 500
- `sortBy` (string, optional): Sort by (CREATED_TIME_DESC, CREATED_TIME_ASC, etc.)

#### Cancel Order

Cancel a specific order.

```bash
curl -X POST "https://your-api-server.com/api/cancel-order" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "orderId": 12345,
    "symbol": "PERP_ETH_USDC"
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `orderId` (integer, required): Order ID to cancel
- `symbol` (string, required): Trading symbol

#### Cancel All Orders

Cancel all outstanding orders (NEW and PARTIAL_FILLED status).

```bash
curl -X POST "https://your-api-server.com/api/cancel-all-orders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx"
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID

#### Close All Positions

Close all open positions using MARKET orders.

```bash
curl -X POST "https://your-api-server.com/api/close-all-positions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx"
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID

#### Settle PnL

Settle realized and unrealized PnL into USDC balance.

```bash
curl -X POST "https://your-api-server.com/api/settle-pnl" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "chainId": 8453
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `chainId` (integer, optional): Chain ID

#### Withdraw USDC

Withdraw USDC from Orderly account.

```bash
curl -X POST "https://your-api-server.com/api/withdraw-usdc" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "walletId": "wal_xxx",
    "amount": "100",
    "token": "USDC",
    "chainId": 80001
  }'
```

**Request Body:**

- `walletId` (string, required): Privy wallet ID
- `amount` (string, required): Amount to withdraw (minimum: 1.001)
- `token` (string, optional): Token symbol, defaults to "USDC"
- `chainId` (integer, optional): Chain ID

## Project Structure

### Core Scripts

- `create_agentic_wallet.py` - Create Privy agentic wallets
- `register_orderly_account.py` - Register wallets with Orderly Network
- `add_orderly_key.py` - Add Orderly authentication keys
- `deposit_usdc.py` - Deposit USDC to Orderly
- `withdraw_usdc.py` - Withdraw USDC from Orderly
- `get_holding.py` - Get current token holdings
- `get_positions.py` - Get open positions
- `create_order.py` - Create trading orders
- `get_orders.py` - Get orders with filters
- `cancel_order.py` - Cancel a specific order
- `cancel_all_orders.py` - Cancel all outstanding orders
- `close_all_positions.py` - Close all open positions
- `settle_pnl.py` - Settle PnL into USDC balance

### Server

- `server.py` - Flask REST API server exposing all operations as HTTP endpoints

### Utilities

- `orderly_auth.py` - Orderly API authentication helpers
- `orderly_db.py` - Database operations for storing Orderly keys
- `orderly_constants.py` - Shared constants and configuration
- `privy_utils.py` - Privy API utility functions

## Error Handling

The scripts will:

- Validate that all required environment variables are set
- Display clear error messages if operations fail
- Show detailed error information from APIs

## Security Notes

- **Never commit your `.env` file** to version control
- Keep your App Secret and Authorization Secret secure
- Use environment variables or secure secret management in production
- Orderly keys are encrypted at rest in the database
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
