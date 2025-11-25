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
 * Get current holding from Orderly account
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-current-holding
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {boolean} options.all - If true, return all tokens even if balance is empty (optional, default: false)
 * @returns {Promise<Object>} - Holding result
 */
async function getHolding(options = {}) {
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
    const includeAll = options.all || false;

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

    console.log("\nFetching current holding from Orderly...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Broker ID: ${brokerId}`);
    console.log(`   Account ID: ${accountId}`);
    console.log(`   Include all tokens: ${includeAll}`);

    // Build query parameters
    const queryParams = includeAll ? "?all=true" : "";
    const path = `/v1/client/holding${queryParams}`;

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
        `Failed to get holding: ${JSON.stringify(data)}`
      );
    }

    if (!data.success) {
      throw new Error(
        `Orderly API returned error: ${JSON.stringify(data)}`
      );
    }

    console.log("\n✅ Holding retrieved successfully!");

    return {
      success: true,
      data: data.data,
      holdings: data.data?.holding || [],
      timestamp: data.timestamp,
      walletAddress: walletAddress,
      accountId: accountId,
    };
  } catch (error) {
    console.error("\n❌ Failed to get holding");
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
      } else if (args[i] === "--all") {
        options.all = true;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node getHolding.js [options]

Options:
  --wallet-id <id>        Privy wallet ID to use (required)
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --all                   Include all tokens even if balance is empty (optional, default: false)
  --help, -h              Show this help message

Examples:
  # Get current holding for a Privy wallet
  node getHolding.js --wallet-id wal_xxx

  # Get holding with wallet address provided
  node getHolding.js --wallet-id wal_xxx --wallet-address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

  # Get all tokens including those with zero balance
  node getHolding.js --wallet-id wal_xxx --all

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

    const result = await getHolding(options);

    // Display holdings in a formatted way
    console.log("\n📊 Current Holdings:");
    console.log("=".repeat(80));

    if (result.holdings.length === 0) {
      console.log("   No holdings found.");
    } else {
      // Calculate total value (if we had prices, but for now just show balances)
      let totalHolding = 0;

      result.holdings.forEach((holding, index) => {
        const available = holding.holding - holding.frozen;
        totalHolding += holding.holding;

        console.log(`\n${index + 1}. ${holding.token}:`);
        console.log(`   Total Holding: ${holding.holding.toLocaleString()}`);
        console.log(`   Frozen: ${holding.frozen.toLocaleString()}`);
        console.log(`   Available: ${available.toLocaleString()}`);
        console.log(`   Pending Short: ${holding.pending_short.toLocaleString()}`);
        console.log(
          `   Updated: ${new Date(holding.updated_time).toLocaleString()}`
        );
      });

      console.log("\n" + "=".repeat(80));
      console.log(`Total Holdings: ${totalHolding.toLocaleString()} (across all tokens)`);
    }

    console.log("\n📝 Summary:");
    console.log(`   Wallet Address: ${result.walletAddress}`);
    console.log(`   Account ID: ${result.accountId}`);
    console.log(`   Number of Tokens: ${result.holdings.length}`);
    console.log(`   Timestamp: ${new Date(result.timestamp).toLocaleString()}`);

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to get holding:", error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { getHolding, getAccountId };

