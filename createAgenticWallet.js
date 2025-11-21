require("dotenv").config();
const { PrivyClient } = require("@privy-io/node");

/**
 * Creates an Agentic wallet using Privy
 *
 * @param {Object} options - Configuration options
 * @param {string} options.policyId - Optional policy ID to assign to the wallet
 * @param {string} options.chainType - Chain type ('ethereum' or 'solana'), defaults to 'ethereum'
 * @returns {Promise<Object>} The created wallet object
 */
async function createAgenticWallet(options = {}) {
  // Validate environment variables
  const appId = process.env.PRIVY_APP_ID;
  const appSecret = process.env.PRIVY_APP_SECRET;
  const authorizationId = process.env.PRIVY_AUTHORIZATION_ID;
  const authorizationSecret = process.env.PRIVY_AUTHORIZATION_SECRET;

  // Initialize Privy client
  const privy = new PrivyClient({
    appId: appId,
    appSecret: appSecret,
  });

  // Prepare wallet creation data
  // The wallet owner_id should be set to the authorization key ID
  const walletData = {
    chain_type: options.chainType || "ethereum",
    owner_id: authorizationId,
    ...(options.policyId && { policy_ids: [options.policyId] }),
  };

  console.log("Creating agentic wallet...");
  console.log("Wallet configuration:", JSON.stringify(walletData, null, 2));

  // Create the agentic wallet using Privy SDK
  const wallet = await privy.wallets().create(walletData);

  console.log("✅ Agentic wallet created successfully!");
  console.log("Wallet details:", JSON.stringify(wallet, null, 2));

  return wallet;
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
      if (args[i] === "--policy-id" && args[i + 1]) {
        options.policyId = args[i + 1];
        i++;
      } else if (args[i] === "--chain-type" && args[i + 1]) {
        options.chainType = args[i + 1];
        i++;
      }
    }

    const wallet = await createAgenticWallet(options);

    console.log("\n📝 Wallet Summary:");
    console.log(`   Wallet ID: ${wallet.id || wallet.wallet_id || "N/A"}`);
    console.log(
      `   Address: ${wallet.address || wallet.addresses?.[0] || "N/A"}`
    );
    console.log(`   Owner ID: ${wallet.owner_id || "N/A"}`);
    console.log(`   Chain Type: ${wallet.chain_type || "N/A"}`);
    if (wallet.policy_ids && wallet.policy_ids.length > 0) {
      console.log(`   Policy IDs: ${wallet.policy_ids.join(", ")}`);
    }

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to create agentic wallet");
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { createAgenticWallet };
