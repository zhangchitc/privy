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
 * Get orders from Orderly account
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-orders
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {string} [options.symbol] - Trading symbol filter (optional)
 * @param {string} [options.side] - Order side filter: BUY or SELL (optional)
 * @param {string} [options.orderType] - Order type filter: LIMIT or MARKET (optional)
 * @param {string} [options.status] - Order status filter: NEW, CANCELLED, PARTIAL_FILLED, FILLED, REJECTED, INCOMPLETE, COMPLETED (optional)
 * @param {string} [options.orderTag] - Order tag filter (optional)
 * @param {number} [options.startTime] - Start time range (13-digit timestamp in milliseconds) (optional)
 * @param {number} [options.endTime] - End time range (13-digit timestamp in milliseconds) (optional)
 * @param {number} [options.page] - Page number (starts from 1) (optional, default: 1)
 * @param {number} [options.size] - Page size (max: 500) (optional, default: 25)
 * @param {string} [options.sortBy] - Sort by: CREATED_TIME_DESC, CREATED_TIME_ASC, UPDATED_TIME_DESC, UPDATED_TIME_ASC (optional)
 * @returns {Promise<Object>} - Orders result
 */
async function getOrders(options = {}) {
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

    console.log("\nFetching orders from Orderly...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Account ID: ${accountId}`);

    // Build query parameters
    const queryParams = new URLSearchParams();
    if (options.symbol) queryParams.append("symbol", options.symbol);
    if (options.side) queryParams.append("side", options.side.toUpperCase());
    if (options.orderType) queryParams.append("order_type", options.orderType.toUpperCase());
    if (options.status) queryParams.append("status", options.status.toUpperCase());
    if (options.orderTag) queryParams.append("order_tag", options.orderTag);
    if (options.startTime) queryParams.append("start_t", options.startTime.toString());
    if (options.endTime) queryParams.append("end_t", options.endTime.toString());
    if (options.page) queryParams.append("page", options.page.toString());
    if (options.size) queryParams.append("size", options.size.toString());
    if (options.sortBy) queryParams.append("sort_by", options.sortBy);

    const queryString = queryParams.toString();
    const path = `/v1/orders${queryString ? `?${queryString}` : ""}`;

    if (queryString) {
      console.log(`   Filters: ${queryString}`);
    }

    // Create authenticated request
    const requestConfig = await createAuthenticatedRequest(
      "GET",
      path,
      null,
      accountId,
      orderlyKey,
      orderlyPrivateKey
    );

    // Make the request
    const response = await fetch(`${ORDERLY_API_URL}${path}`, requestConfig);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        `Failed to get orders: ${JSON.stringify(data)}`
      );
    }

    if (!data.success) {
      throw new Error(
        `Orderly API returned error: ${JSON.stringify(data)}`
      );
    }

    console.log("\n✅ Orders retrieved successfully!");

    return {
      success: true,
      data: data.data,
      orders: data.data?.rows || [],
      meta: data.data?.meta || {},
      timestamp: data.timestamp,
      walletAddress: walletAddress,
      accountId: accountId,
    };
  } catch (error) {
    console.error("\n❌ Failed to get orders");
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
      } else if (args[i] === "--symbol" && args[i + 1]) {
        options.symbol = args[i + 1];
        i++;
      } else if (args[i] === "--side" && args[i + 1]) {
        options.side = args[i + 1];
        i++;
      } else if (args[i] === "--order-type" && args[i + 1]) {
        options.orderType = args[i + 1];
        i++;
      } else if (args[i] === "--status" && args[i + 1]) {
        options.status = args[i + 1];
        i++;
      } else if (args[i] === "--order-tag" && args[i + 1]) {
        options.orderTag = args[i + 1];
        i++;
      } else if (args[i] === "--start-time" && args[i + 1]) {
        options.startTime = parseInt(args[i + 1]);
        i++;
      } else if (args[i] === "--end-time" && args[i + 1]) {
        options.endTime = parseInt(args[i + 1]);
        i++;
      } else if (args[i] === "--page" && args[i + 1]) {
        options.page = parseInt(args[i + 1]);
        i++;
      } else if (args[i] === "--size" && args[i + 1]) {
        options.size = parseInt(args[i + 1]);
        i++;
      } else if (args[i] === "--sort-by" && args[i + 1]) {
        options.sortBy = args[i + 1];
        i++;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node getOrders.js [options]

Required Options:
  --wallet-id <id>        Privy wallet ID to use (required)

Optional Options:
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --symbol <symbol>        Trading symbol filter (e.g., "PERP_ETH_USDC")
  --side <side>            Order side filter: BUY or SELL
  --order-type <type>       Order type filter: LIMIT or MARKET
  --status <status>         Order status filter: NEW, CANCELLED, PARTIAL_FILLED, FILLED, REJECTED, INCOMPLETE, COMPLETED
  --order-tag <tag>         Order tag filter
  --start-time <timestamp>  Start time range (13-digit timestamp in milliseconds)
  --end-time <timestamp>    End time range (13-digit timestamp in milliseconds)
  --page <page>             Page number (starts from 1, default: 1)
  --size <size>             Page size (max: 500, default: 25)
  --sort-by <sort>          Sort by: CREATED_TIME_DESC, CREATED_TIME_ASC, UPDATED_TIME_DESC, UPDATED_TIME_ASC
  --help, -h                 Show this help message

Status Values:
  - NEW: New orders
  - CANCELLED: Cancelled orders
  - PARTIAL_FILLED: Partially filled orders
  - FILLED: Fully filled orders
  - REJECTED: Rejected orders
  - INCOMPLETE: NEW + PARTIAL_FILLED (bundled status)
  - COMPLETED: CANCELLED + FILLED (bundled status)

Examples:
  # Get all orders for a Privy wallet
  node getOrders.js --wallet-id wal_xxx

  # Get orders for a specific symbol
  node getOrders.js --wallet-id wal_xxx --symbol "PERP_ETH_USDC"

  # Get only BUY orders
  node getOrders.js --wallet-id wal_xxx --side BUY

  # Get incomplete orders (NEW + PARTIAL_FILLED)
  node getOrders.js --wallet-id wal_xxx --status INCOMPLETE

  # Get orders with pagination
  node getOrders.js --wallet-id wal_xxx --page 1 --size 50

  # Get orders sorted by creation time (descending)
  node getOrders.js --wallet-id wal_xxx --sort-by CREATED_TIME_DESC

  # Get orders within a time range
  node getOrders.js --wallet-id wal_xxx --start-time 1653563963000 --end-time 1653564213000

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

    const result = await getOrders(options);

    // Display orders in a formatted way
    console.log("\n📋 Orders:");
    console.log("=".repeat(100));

    if (result.orders.length === 0) {
      console.log("   No orders found.");
    } else {
      // Display pagination info
      if (result.meta.total !== undefined) {
        console.log(`\nTotal Orders: ${result.meta.total}`);
        console.log(`Page: ${result.meta.current_page || 1} of ${Math.ceil((result.meta.total || 0) / (result.meta.records_per_page || 25))}`);
        console.log(`Records per page: ${result.meta.records_per_page || 25}`);
      }

      result.orders.forEach((order, index) => {
        console.log(`\n${index + 1}. Order #${order.order_id}:`);
        console.log(`   Symbol: ${order.symbol}`);
        console.log(`   Side: ${order.side}`);
        console.log(`   Type: ${order.type}`);
        console.log(`   Status: ${order.status}`);
        console.log(`   Price: ${order.price}`);
        console.log(`   Quantity: ${order.quantity}`);
        if (order.amount !== null && order.amount !== undefined) {
          console.log(`   Amount: ${order.amount}`);
        }
        console.log(`   Executed Quantity: ${order.executed_quantity}`);
        console.log(`   Total Executed Quantity: ${order.total_executed_quantity}`);
        console.log(`   Visible Quantity: ${order.visible_quantity}`);
        console.log(`   Average Executed Price: ${order.average_executed_price}`);
        console.log(`   Total Fee: ${order.total_fee} ${order.fee_asset}`);
        if (order.client_order_id !== null && order.client_order_id !== undefined) {
          console.log(`   Client Order ID: ${order.client_order_id}`);
        }
        console.log(`   Realized PnL: ${order.realized_pnl}`);
        console.log(`   Created: ${new Date(order.created_time).toLocaleString()}`);
        console.log(`   Updated: ${new Date(order.updated_time).toLocaleString()}`);
      });
    }

    console.log("\n" + "=".repeat(100));
    console.log("\n📝 Summary:");
    console.log(`   Wallet Address: ${result.walletAddress}`);
    console.log(`   Account ID: ${result.accountId}`);
    console.log(`   Number of Orders: ${result.orders.length}`);
    if (result.meta.total !== undefined) {
      console.log(`   Total Orders: ${result.meta.total}`);
    }
    console.log(`   Timestamp: ${new Date(result.timestamp).toLocaleString()}`);

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to get orders:", error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { getOrders, getAccountId };

