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
 * Create an order on Orderly Network using Privy agentic wallet
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/create-order
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {string} options.symbol - Trading symbol (e.g., "PERP_ETH_USDC")
 * @param {string} options.orderType - Order type: "LIMIT", "MARKET", "IOC", "FOK", "POST_ONLY", "ASK", "BID"
 * @param {string} options.side - Order side: "BUY" or "SELL"
 * @param {number} [options.orderPrice] - Order price (required for LIMIT, IOC, FOK, POST_ONLY)
 * @param {number} [options.orderQuantity] - Order quantity in base currency
 * @param {number} [options.orderAmount] - Order amount in quote currency (for MARKET/BID/ASK orders)
 * @param {number} [options.visibleQuantity] - Visible quantity on orderbook (default: order_quantity)
 * @param {boolean} [options.reduceOnly] - Reduce only flag (default: false)
 * @param {number} [options.slippage] - Slippage tolerance for MARKET orders
 * @param {string} [options.clientOrderId] - Custom client order ID (36 chars max, unique)
 * @param {string} [options.orderTag] - Order tag
 * @param {number} [options.level] - Level for BID/ASK orders (0-4)
 * @param {boolean} [options.postOnlyAdjust] - Price adjustment for POST_ONLY orders
 * @returns {Promise<Object>} - Order creation result
 */
async function createOrder(options = {}) {
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

    // Extract order parameters
    const {
      symbol,
      orderType,
      side,
      orderPrice,
      orderQuantity,
      orderAmount,
      visibleQuantity,
      reduceOnly = false,
      slippage,
      clientOrderId,
      orderTag,
      level,
      postOnlyAdjust,
    } = options;

    console.log("\nPreparing order creation...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Account ID: ${accountId}`);
    console.log(`   Symbol: ${symbol}`);
    console.log(`   Order Type: ${orderType}`);
    console.log(`   Side: ${side}`);

    // Validate required fields
    if (!symbol || !orderType || !side) {
      throw new Error(
        "Missing required fields: symbol, orderType, and side are required"
      );
    }

    // Validate order type
    const validOrderTypes = [
      "LIMIT",
      "MARKET",
      "IOC",
      "FOK",
      "POST_ONLY",
      "ASK",
      "BID",
    ];

    if (!validOrderTypes.includes(orderType.toUpperCase())) {
      throw new Error(
        `Invalid order type: ${orderType}. Must be one of: ${validOrderTypes.join(
          ", "
        )}`
      );
    }

    // Validate side
    if (!["BUY", "SELL"].includes(side.toUpperCase())) {
      throw new Error(`Invalid side: ${side}. Must be BUY or SELL`);
    }

    // Validate order_price requirement for certain order types
    const orderTypeUpper = orderType.toUpperCase();
    if (
      ["LIMIT", "IOC", "FOK", "POST_ONLY"].includes(orderTypeUpper) &&
      orderPrice === undefined
    ) {
      throw new Error(`orderPrice is required for ${orderType} orders`);
    }

    // Validate order_quantity or order_amount
    if (orderQuantity === undefined && orderAmount === undefined) {
      throw new Error("Either orderQuantity or orderAmount must be provided");
    }

    // Validate MARKET/BID/ASK order requirements
    if (["MARKET", "BID", "ASK"].includes(orderTypeUpper)) {
      if (side.toUpperCase() === "SELL" && orderAmount !== undefined) {
        throw new Error(
          "orderAmount is not supported for SELL orders with MARKET/BID/ASK order types"
        );
      }
      if (side.toUpperCase() === "BUY" && orderQuantity !== undefined) {
        throw new Error(
          "orderQuantity is not supported for BUY orders with MARKET/BID/ASK order types"
        );
      }
    }

    // Build request body
    const requestBody = {
      symbol: symbol,
      order_type: orderType.toUpperCase(),
      side: side.toUpperCase(),
    };

    // Add optional fields
    if (orderPrice !== undefined) {
      requestBody.order_price = orderPrice;
    }
    if (orderQuantity !== undefined) {
      requestBody.order_quantity = orderQuantity;
    }
    if (orderAmount !== undefined) {
      requestBody.order_amount = orderAmount;
    }
    if (visibleQuantity !== undefined) {
      requestBody.visible_quantity = visibleQuantity;
    }
    if (reduceOnly !== undefined) {
      requestBody.reduce_only = reduceOnly;
    }
    if (slippage !== undefined) {
      requestBody.slippage = slippage;
    }
    if (clientOrderId !== undefined) {
      requestBody.client_order_id = clientOrderId;
    }
    if (orderTag !== undefined) {
      requestBody.order_tag = orderTag;
    }
    if (level !== undefined) {
      requestBody.level = level;
    }
    if (postOnlyAdjust !== undefined) {
      requestBody.post_only_adjust = postOnlyAdjust;
    }

    console.log("\nOrder parameters:", JSON.stringify(requestBody, null, 2));

    const path = "/v1/order";
    const requestConfig = await createAuthenticatedRequest(
      "POST",
      path,
      requestBody,
      accountId,
      orderlyKey,
      orderlyPrivateKey
    );

    const response = await fetch(`${ORDERLY_API_URL}${path}`, requestConfig);
    const data = await response.json();

    // Check both HTTP status and success field in response body
    if (!response.ok) {
      throw new Error(`Failed to create order: ${JSON.stringify(data)}`);
    }

    if (!data.success) {
      throw new Error(`Order creation failed: ${JSON.stringify(data)}`);
    }

    console.log("\n✅ Order created successfully!");
    console.log("Response:", JSON.stringify(data, null, 2));

    return {
      success: true,
      data: data.data,
      orderId: data.data?.order_id,
      clientOrderId: data.data?.client_order_id,
      walletAddress: walletAddress,
      accountId: accountId,
    };
  } catch (error) {
    console.error("\n❌ Failed to create order");
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
      } else if (args[i] === "--order-type" && args[i + 1]) {
        options.orderType = args[i + 1];
        i++;
      } else if (args[i] === "--side" && args[i + 1]) {
        options.side = args[i + 1];
        i++;
      } else if (args[i] === "--order-price" && args[i + 1]) {
        options.orderPrice = parseFloat(args[i + 1]);
        i++;
      } else if (args[i] === "--order-quantity" && args[i + 1]) {
        options.orderQuantity = parseFloat(args[i + 1]);
        i++;
      } else if (args[i] === "--order-amount" && args[i + 1]) {
        options.orderAmount = parseFloat(args[i + 1]);
        i++;
      } else if (args[i] === "--visible-quantity" && args[i + 1]) {
        options.visibleQuantity = parseFloat(args[i + 1]);
        i++;
      } else if (args[i] === "--reduce-only") {
        options.reduceOnly = true;
      } else if (args[i] === "--slippage" && args[i + 1]) {
        options.slippage = parseFloat(args[i + 1]);
        i++;
      } else if (args[i] === "--client-order-id" && args[i + 1]) {
        options.clientOrderId = args[i + 1];
        i++;
      } else if (args[i] === "--order-tag" && args[i + 1]) {
        options.orderTag = args[i + 1];
        i++;
      } else if (args[i] === "--level" && args[i + 1]) {
        options.level = parseInt(args[i + 1]);
        i++;
      } else if (args[i] === "--post-only-adjust") {
        options.postOnlyAdjust = true;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node createOrder.js [options]

Required Options:
  --wallet-id <id>        Privy wallet ID to use (required)
  --symbol <symbol>       Trading symbol (e.g., "PERP_ETH_USDC") (required)
  --order-type <type>     Order type: LIMIT, MARKET, IOC, FOK, POST_ONLY, ASK, BID (required)
  --side <side>           Order side: BUY or SELL (required)

Optional Options:
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --order-price <price>    Order price (required for LIMIT/IOC/FOK/POST_ONLY)
  --order-quantity <qty>   Order quantity in base currency
  --order-amount <amount>  Order amount in quote currency (for MARKET/BID/ASK BUY orders)
  --visible-quantity <qty> Visible quantity on orderbook (default: order_quantity)
  --reduce-only            Reduce only flag (default: false)
  --slippage <slippage>    Slippage tolerance for MARKET orders
  --client-order-id <id>   Custom client order ID (36 chars max, unique)
  --order-tag <tag>        Order tag
  --level <level>          Level for BID/ASK orders (0-4)
  --post-only-adjust       Price adjustment for POST_ONLY orders
  --help, -h               Show this help message

Examples:
  # LIMIT BUY order
  node createOrder.js --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type LIMIT --side BUY --order-price 2000 --order-quantity 0.1

  # MARKET BUY order (using orderAmount)
  node createOrder.js --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type MARKET --side BUY --order-amount 100

  # LIMIT SELL order
  node createOrder.js --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type LIMIT --side SELL --order-price 2100 --order-quantity 0.05

  # LIMIT BUY order with reduce-only
  node createOrder.js --wallet-id wal_xxx --symbol "PERP_ETH_USDC" --order-type LIMIT --side BUY --order-price 2000 --order-quantity 0.1 --reduce-only

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

    const result = await createOrder(options);

    console.log("\n📝 Order Summary:");
    console.log(`   Wallet Address: ${result.walletAddress}`);
    console.log(`   Account ID: ${result.accountId}`);
    console.log(`   Order ID: ${result.orderId}`);
    if (result.clientOrderId) {
      console.log(`   Client Order ID: ${result.clientOrderId}`);
    }

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to create order:", error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { createOrder, getAccountId };

