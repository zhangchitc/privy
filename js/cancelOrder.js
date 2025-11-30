require("dotenv").config();
const { PrivyClient } = require("@privy-io/node");
const { ethers } = require("ethers");
const {
  createAuthenticatedRequest,
  hexToPrivateKey,
} = require("./orderly-auth");

// Use native fetch in Node.js 18+ or fallback to node-fetch
let fetch;
if (typeof globalThis !== "undefined" && globalThis.fetch) {
  fetch = globalThis.fetch;
} else {
  try {
    fetch = require("node-fetch");
  } catch (e) {
    throw new Error(
      "fetch is not available. Please install node-fetch: npm install node-fetch"
    );
  }
}

// Configuration
const ORDERLY_API_URL = "https://api.orderly.org"; // or https://testnet-api.orderly.org for testnet
const BROKER_ID = "woofi_pro";

/**
 * Generate Orderly account ID
 * Based on Orderly documentation: accountId = keccak256(abi.encode(address, keccak256(abi.encodePacked(brokerId))))
 *
 * @param {string} address - User wallet address
 * @param {string} brokerId - Broker ID
 * @returns {string} - Account ID as bytes32 hex string
 */
function getAccountId(address, brokerId) {
  const abiCoder = ethers.AbiCoder.defaultAbiCoder();
  // keccak256(abi.encodePacked(brokerId)) - using solidityPackedKeccak256 for ABI-encoded string
  const brokerIdHash = ethers.solidityPackedKeccak256(["string"], [brokerId]);
  // keccak256(abi.encode(address, brokerIdHash))
  return ethers.keccak256(
    abiCoder.encode(["address", "bytes32"], [address, brokerIdHash])
  );
}

/**
 * Cancel an order on Orderly Network using Privy agentic wallet
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/cancel-order
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {number} options.orderId - Order ID to cancel (required)
 * @param {string} options.symbol - Trading symbol (e.g., "PERP_ETH_USDC") (required)
 * @returns {Promise<Object>} - Cancellation result
 */
async function cancelOrder(options = {}) {
  try {
    // Validate environment variables
    const appId = process.env.PRIVY_APP_ID;
    const appSecret = process.env.PRIVY_APP_SECRET;

    if (!appId || !appSecret) {
      throw new Error(
        "Missing required environment variables. Please ensure the following are set in your .env file:\n" +
          "- PRIVY_APP_ID\n" +
          "- PRIVY_APP_SECRET"
      );
    }

    if (!options.walletId) {
      throw new Error("Wallet ID is required. Use --wallet-id <wallet_id>");
    }

    if (!options.orderId) {
      throw new Error("Order ID is required. Use --order-id <order_id>");
    }

    if (!options.symbol) {
      throw new Error("Symbol is required. Use --symbol <symbol>");
    }

    // Get Orderly credentials
    const orderlyKey = process.env.ORDERLY_KEY;
    if (!orderlyKey) {
      throw new Error(
        "ORDERLY_KEY environment variable is required (should be in format 'ed25519:...')"
      );
    }

    const orderlyPrivateKeyHex = process.env.ORDERLY_PRIVATE_KEY;
    if (!orderlyPrivateKeyHex) {
      throw new Error(
        "ORDERLY_PRIVATE_KEY environment variable is required (ed25519 private key in hex format)"
      );
    }

    // Convert hex string to Uint8Array
    const orderlyPrivateKey = hexToPrivateKey(orderlyPrivateKeyHex);

    // Initialize Privy client
    const privy = new PrivyClient({
      appId: appId,
      appSecret: appSecret,
    });

    // Configuration
    const brokerId = BROKER_ID;
    const orderId = parseInt(options.orderId, 10);
    const symbol = options.symbol;

    // Get wallet address if not provided
    let walletAddress = options.walletAddress;
    if (!walletAddress) {
      console.log("Fetching wallet details...");
      const wallet = await privy.wallets().get(options.walletId);
      walletAddress = wallet.address || wallet.addresses?.[0];
      if (!walletAddress) {
        throw new Error(
          "Could not determine wallet address from wallet object"
        );
      }
      console.log(`   Wallet Address: ${walletAddress}`);
    }

    // Derive Orderly account ID from wallet address and broker ID
    const accountId = getAccountId(walletAddress, brokerId);

    console.log("\nPreparing order cancellation...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Account ID: ${accountId}`);
    console.log(`   Order ID: ${orderId}`);
    console.log(`   Symbol: ${symbol}`);

    // Build query parameters
    const queryParams = new URLSearchParams();
    queryParams.append("order_id", orderId.toString());
    queryParams.append("symbol", symbol);

    const path = `/v1/order?${queryParams.toString()}`;

    // Create authenticated request
    const requestConfig = await createAuthenticatedRequest(
      "DELETE",
      path,
      null,
      accountId,
      orderlyKey,
      orderlyPrivateKey
    );

    // Make the request
    const response = await fetch(`${ORDERLY_API_URL}${path}`, requestConfig);
    const data = await response.json();

    // Check both HTTP status and success field in response body
    if (!response.ok) {
      throw new Error(`Failed to cancel order: ${JSON.stringify(data)}`);
    }

    if (!data.success) {
      throw new Error(`Cancel order failed: ${JSON.stringify(data)}`);
    }

    console.log("\n✅ Order cancelled successfully!");
    console.log("Response:", JSON.stringify(data, null, 2));

    return {
      success: true,
      data: data.data,
      status: data.data?.status,
      orderId: orderId,
      symbol: symbol,
      walletAddress: walletAddress,
      accountId: accountId,
    };
  } catch (error) {
    console.error("\n❌ Failed to cancel order");
    if (error.message) {
      console.error("Error:", error.message);
    } else {
      console.error(error);
    }
    throw error;
  }
}

/**
 * Main execution function
 */
async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const options = {};

    // Simple argument parsing
    for (let i = 0; i < args.length; i++) {
      if (args[i] === "--wallet-id" && args[i + 1]) {
        options.walletId = args[i + 1];
        i++;
      } else if (args[i] === "--wallet-address" && args[i + 1]) {
        options.walletAddress = args[i + 1];
        i++;
      } else if (args[i] === "--order-id" && args[i + 1]) {
        options.orderId = args[i + 1];
        i++;
      } else if (args[i] === "--symbol" && args[i + 1]) {
        options.symbol = args[i + 1];
        i++;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node cancelOrder.js [options]

Required Options:
  --wallet-id <id>        Privy wallet ID to use (required)
  --order-id <id>         Order ID to cancel (required)
  --symbol <symbol>       Trading symbol (e.g., "PERP_ETH_USDC") (required)

Optional Options:
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --help, -h              Show this help message

Examples:
  # Cancel order by order ID
  node cancelOrder.js --wallet-id wal_xxx --order-id 12345 --symbol "PERP_ETH_USDC"

  # Cancel order with wallet address provided
  node cancelOrder.js --wallet-id wal_xxx --wallet-address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --order-id 12345 --symbol "PERP_ETH_USDC"

Environment Variables:
  PRIVY_APP_ID              Privy App ID (required)
  PRIVY_APP_SECRET          Privy App Secret (required)
  ORDERLY_KEY               Orderly public key (ed25519:...) (required)
  ORDERLY_PRIVATE_KEY       Orderly private key in hex format (required)

Note: Orderly account ID is automatically derived from wallet address and broker ID.
        `);
        process.exit(0);
      }
    }

    const result = await cancelOrder(options);

    console.log("\n📝 Cancellation Summary:");
    console.log(`   Wallet Address: ${result.walletAddress}`);
    console.log(`   Account ID: ${result.accountId}`);
    console.log(`   Order ID: ${result.orderId}`);
    console.log(`   Symbol: ${result.symbol}`);
    console.log(`   Status: ${result.status}`);

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to cancel order:", error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { cancelOrder, getAccountId };

