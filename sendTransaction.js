require("dotenv").config();
const { PrivyClient } = require("@privy-io/node");

/**
 * Sends a transaction from an agentic wallet using Privy
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The wallet ID to send from
 * @param {string} options.to - Recipient address
 * @param {string} options.value - Amount in wei (optional, defaults to 0.001 ETH)
 * @param {string} options.chainId - Chain ID (optional, defaults to Sepolia testnet: 11155111)
 * @returns {Promise<Object>} The transaction response
 */
async function sendTransaction(options = {}) {
  // Validate environment variables
  const appId = process.env.PRIVY_APP_ID;
  const appSecret = process.env.PRIVY_APP_SECRET;
  const authorizationId = process.env.PRIVY_AUTHORIZATION_ID;
  const authorizationSecret = process.env.PRIVY_AUTHORIZATION_SECRET;

  if (!options.walletId) {
    throw new Error("Wallet ID is required. Use --wallet-id <wallet_id>");
  }

  if (!options.to) {
    throw new Error("Recipient address is required. Use --to <address>");
  }

  // Initialize Privy client
  const privy = new PrivyClient({
    appId: appId,
    appSecret: appSecret,
  });

  // Default to Sepolia testnet (chain ID: 11155111)
  // Other testnet options:
  // - Goerli: 5 (deprecated, use Sepolia)
  // - Base Sepolia: 84532
  // - Polygon Mumbai: 80001
  const chainIdDecimal = options.chainId || "11155111"; // Sepolia testnet
  const valueDecimal = options.value || "1000000000000000"; // 0.001 ETH in wei

  // Convert to hex format (Privy requires hex values with "0x" prefix)
  const chainIdHex = `0x${BigInt(chainIdDecimal).toString(16)}`;
  const valueHex = `0x${BigInt(valueDecimal).toString(16)}`;

  // Create authorization context with the authorization private key
  const authorizationContext = {
    authorization_private_keys: [authorizationSecret],
  };

  console.log("Preparing transaction...");
  console.log(`   Wallet ID: ${options.walletId}`);
  console.log(`   To: ${options.to}`);
  console.log(
    `   Value: ${valueDecimal} wei (${
      Number(valueDecimal) / 1e18
    } ETH) = ${valueHex}`
  );
  console.log(
    `   Chain ID: ${chainIdDecimal} (${getChainName(
      chainIdDecimal
    )}) = ${chainIdHex}`
  );

  try {
    // Send transaction using Privy SDK
    // The caip2 format is: eip155:<chain_id> (decimal format)
    const response = await privy
      .wallets()
      .ethereum()
      .sendTransaction(options.walletId, {
        authorization_context: authorizationContext,
        caip2: `eip155:${chainIdDecimal}`,
        params: {
          transaction: {
            chain_id: chainIdHex, // Must be hex format with "0x" prefix
            to: options.to,
            value: valueHex, // Must be hex format with "0x" prefix
            // Optional: You can add data for contract calls
            // data: "0x..."
          },
        },
      });

    console.log("\n✅ Transaction sent successfully!");
    console.log("Transaction details:", JSON.stringify(response, null, 2));

    return response;
  } catch (error) {
    console.error("\n❌ Failed to send transaction");
    console.error(error);
    process.exit(1);
  }
}

/**
 * Get human-readable chain name
 */
function getChainName(chainId) {
  const chains = {
    1: "Ethereum Mainnet",
    5: "Goerli (deprecated)",
    11155111: "Sepolia Testnet",
    84532: "Base Sepolia",
    80001: "Polygon Mumbai",
  };
  return chains[chainId] || `Chain ${chainId}`;
}

/**
 * Main execution function
 */
async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const options = {};

    for (let i = 0; i < args.length; i++) {
      if (args[i] === "--wallet-id" && args[i + 1]) {
        options.walletId = args[i + 1];
        i++;
      } else if (args[i] === "--to" && args[i + 1]) {
        options.to = args[i + 1];
        i++;
      } else if (args[i] === "--value" && args[i + 1]) {
        options.value = args[i + 1];
        i++;
      } else if (args[i] === "--chain-id" && args[i + 1]) {
        options.chainId = args[i + 1];
        i++;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node sendTransaction.js [options]

Options:
  --wallet-id <id>     Wallet ID to send from (required)
  --to <address>       Recipient Ethereum address (required)
  --value <wei>        Amount in wei (optional, default: 1000000000000000 = 0.001 ETH)
  --chain-id <id>      Chain ID (optional, default: 11155111 = Sepolia testnet)
  --help, -h           Show this help message

Examples:
  # Send 0.001 ETH on Sepolia testnet
  node sendTransaction.js --wallet-id wal_xxx --to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

  # Send custom amount on Base Sepolia
  node sendTransaction.js --wallet-id wal_xxx --to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --value 2000000000000000 --chain-id 84532

Testnet Chain IDs:
  - Sepolia: 11155111 (recommended)
  - Base Sepolia: 84532
  - Polygon Mumbai: 80001
  - Goerli: 5 (deprecated)

Note: Make sure your wallet has testnet ETH before sending transactions!
        `);
        process.exit(0);
      }
    }

    const result = await sendTransaction(options);

    console.log("\n📝 Transaction Summary:");
    console.log(
      `   Transaction Hash: ${result.transaction_hash || result.hash || "N/A"}`
    );
    console.log(`   Status: ${result.status || "pending"}`);
    if (result.block_number) {
      console.log(`   Block Number: ${result.block_number}`);
    }

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to send transaction");
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { sendTransaction };
