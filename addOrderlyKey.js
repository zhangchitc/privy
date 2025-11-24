require("dotenv").config();
const { PrivyClient } = require("@privy-io/node");
const { getPublicKey, utils } = require("@noble/ed25519");
const bs58 = require("bs58");
const fs = require("fs");
const path = require("path");

// Use webcrypto if available for @noble/ed25519
if (typeof globalThis !== "undefined" && !globalThis.crypto) {
  const { webcrypto } = require("node:crypto");
  globalThis.crypto = webcrypto;
}

// Configuration
const ORDERLY_API_URL = "https://api.orderly.org"; // or https://testnet-api.orderly.org for testnet
const CHAIN_ID = process.env.CHAIN_ID ? parseInt(process.env.CHAIN_ID) : 80001; // Default: Polygon Mumbai testnet
const BROKER_ID = "woofi_pro";
const VERIFYING_CONTRACT = "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC";

/**
 * Generate an ed25519 key pair and encode the public key
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/wallet-authentication
 *
 * @returns {Promise<Object>} - Object with orderlyKey (public key) and privateKeyHex (private key in hex format)
 */
async function generateOrderlyKey() {
  const privateKey = utils.randomPrivateKey();
  const publicKey = await getPublicKey(privateKey);

  // Encode public key using base58 (as shown in Orderly documentation examples)
  const encodedKey = bs58.encode(publicKey);
  const orderlyKey = `ed25519:${encodedKey}`;

  // Convert private key to hex format for storage
  const privateKeyHex = Buffer.from(privateKey).toString("hex");

  return {
    orderlyKey: orderlyKey,
    privateKeyHex: privateKeyHex,
  };
}

/**
 * Add Orderly Key for a Privy wallet
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/wallet-authentication
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {number} options.chainId - The chain ID (optional, defaults to CHAIN_ID)
 * @param {string} options.brokerId - The broker ID (optional, defaults to BROKER_ID)
 * @returns {Promise<Object>} - Result with generated orderlyKey
 */
async function addOrderlyKey(options = {}) {
  // Validate environment variables
  const appId = process.env.PRIVY_APP_ID;
  const appSecret = process.env.PRIVY_APP_SECRET;
  const authorizationId = process.env.PRIVY_AUTHORIZATION_ID;
  const authorizationSecret = process.env.PRIVY_AUTHORIZATION_SECRET;

  if (!appId || !appSecret) {
    throw new Error(
      "Missing required environment variables. Please ensure the following are set in your .env file:\n" +
        "- PRIVY_APP_ID\n" +
        "- PRIVY_APP_SECRET"
    );
  }

  if (!authorizationId || !authorizationSecret) {
    throw new Error(
      "Missing authorization credentials. Please ensure the following are set in your .env file:\n" +
        "- PRIVY_AUTHORIZATION_ID\n" +
        "- PRIVY_AUTHORIZATION_SECRET"
    );
  }

  if (!options.walletId) {
    throw new Error("Wallet ID is required. Use --wallet-id <wallet_id>");
  }

  // Initialize Privy client
  const privy = new PrivyClient({
    appId: appId,
    appSecret: appSecret,
  });

  // Configuration
  const chainId = options.chainId || CHAIN_ID;
  const chainIdNumber = parseInt(chainId, 10);
  const chainIdHex = `0x${BigInt(chainId).toString(16)}`;
  const brokerId = options.brokerId || BROKER_ID;
  const scope = "read,trading";
  const expirationDays = 365;

  // Create authorization context with the authorization private key
  const authorizationContext = {
    authorization_private_keys: [authorizationSecret],
  };

  try {
    // Get wallet address if not provided
    let walletAddress = options.walletAddress;
    if (!walletAddress) {
      console.log("Fetching wallet details...");
      const wallet = await privy.wallets().get(options.walletId);

      if (!wallet) {
        throw new Error(`Wallet with ID ${options.walletId} not found`);
      }

      walletAddress =
        wallet.address ||
        wallet.addresses?.[0]?.address ||
        wallet.addresses?.[0];

      if (!walletAddress) {
        throw new Error(
          "Could not determine wallet address from wallet object"
        );
      }
      console.log(`   Wallet Address: ${walletAddress}`);
    }

    console.log("\nAdding Orderly Key for Privy wallet...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Chain ID: ${chainId} (${chainIdHex})`);
    console.log(`   Broker ID: ${brokerId}`);

    // Generate ed25519 key pair
    console.log("\nGenerating ed25519 key pair...");
    const keyPair = await generateOrderlyKey();
    const orderlyKey = keyPair.orderlyKey;
    const orderlyPrivateKeyHex = keyPair.privateKeyHex;

    console.log(`   Generated Orderly Key: ${orderlyKey}`);
    console.log(`   Generated Orderly Private Key: ${orderlyPrivateKeyHex}`);

    // Create EIP-712 message for adding Orderly Key
    const timestamp = Date.now();
    const expiration = timestamp + expirationDays * 24 * 60 * 60 * 1000; // Convert days to milliseconds

    const message = {
      brokerId: brokerId,
      chainId: chainIdNumber,
      orderlyKey: orderlyKey,
      scope: scope,
      timestamp: timestamp,
      expiration: expiration,
    };

    // Create EIP-712 domain
    const domain = {
      name: "Orderly",
      version: "1",
      chainId: chainIdHex,
      verifyingContract: VERIFYING_CONTRACT,
    };

    // Create EIP-712 types
    const typedData = {
      domain: domain,
      message: message,
      primary_type: "AddOrderlyKey",
      types: {
        EIP712Domain: [
          { name: "name", type: "string" },
          { name: "version", type: "string" },
          { name: "chainId", type: "uint256" },
          { name: "verifyingContract", type: "address" },
        ],
        AddOrderlyKey: [
          { name: "brokerId", type: "string" },
          { name: "chainId", type: "uint256" },
          { name: "orderlyKey", type: "string" },
          { name: "scope", type: "string" },
          { name: "timestamp", type: "uint64" },
          { name: "expiration", type: "uint64" },
        ],
      },
    };

    console.log("\nSigning EIP-712 message...");
    console.log("Message:", JSON.stringify(message, null, 2));

    // Sign the EIP-712 message using Privy
    const signatureResponse = await privy
      .wallets()
      .ethereum()
      .signTypedData(options.walletId, {
        authorization_context: authorizationContext,
        params: {
          typed_data: typedData,
        },
      });

    const signature = signatureResponse.signature;
    console.log(`\n✅ Signature generated: ${signature}`);

    // Add Orderly Key
    // Endpoint: /v1/orderly_key
    console.log("\nAdding Orderly Key to Orderly...");
    const response = await fetch(`${ORDERLY_API_URL}/v1/orderly_key`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        signature: signature,
        userAddress: walletAddress,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(`Failed to add Orderly Key: ${JSON.stringify(data)}`);
    }

    console.log("\n✅ Orderly Key added successfully!");
    console.log("Response:", JSON.stringify(data, null, 2));

    // Save Orderly Key and Private Key to .env file
    const envPath = path.join(process.cwd(), ".env");
    let envContent = "";

    // Read existing .env file if it exists
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, "utf8");
    }

    // Check if ORDERLY_KEY already exists in .env
    const hasOrderlyKey = /^ORDERLY_KEY=/.test(envContent);
    const hasOrderlyPrivateKey = /^ORDERLY_PRIVATE_KEY=/.test(envContent);

    // Update or append ORDERLY_KEY
    if (hasOrderlyKey) {
      envContent = envContent.replace(
        /^ORDERLY_KEY=.*$/m,
        `ORDERLY_KEY=${orderlyKey}`
      );
    } else {
      envContent +=
        (envContent && !envContent.endsWith("\n") ? "\n" : "") +
        `ORDERLY_KEY=${orderlyKey}\n`;
    }

    // Update or append ORDERLY_PRIVATE_KEY
    if (hasOrderlyPrivateKey) {
      envContent = envContent.replace(
        /^ORDERLY_PRIVATE_KEY=.*$/m,
        `ORDERLY_PRIVATE_KEY=${orderlyPrivateKeyHex}`
      );
    } else {
      envContent += `ORDERLY_PRIVATE_KEY=${orderlyPrivateKeyHex}\n`;
    }

    // Write back to .env file
    fs.writeFileSync(envPath, envContent, "utf8");

    console.log("\n✅ Saved to .env file:");
    console.log(`   ORDERLY_KEY=${orderlyKey}`);
    console.log(`   ORDERLY_PRIVATE_KEY=${orderlyPrivateKeyHex}`);

    return {
      success: true,
      data: data,
      userAddress: walletAddress,
      orderlyKey: orderlyKey,
      orderlyPrivateKeyHex: orderlyPrivateKeyHex,
    };
  } catch (error) {
    console.error("\n❌ Failed to add Orderly Key");
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

    for (let i = 0; i < args.length; i++) {
      if (args[i] === "--wallet-id" && args[i + 1]) {
        options.walletId = args[i + 1];
        i++;
      } else if (args[i] === "--wallet-address" && args[i + 1]) {
        options.walletAddress = args[i + 1];
        i++;
      } else if (args[i] === "--chain-id" && args[i + 1]) {
        options.chainId = args[i + 1];
        i++;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node addOrderlyKey.js [options]

Options:
  --wallet-id <id>        Privy wallet ID to use (required)
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --chain-id <id>         Chain ID (optional, default: 80001 = Polygon Mumbai)
  --help, -h              Show this help message

Examples:
  # Add Orderly Key for a Privy wallet
  node addOrderlyKey.js --wallet-id wal_xxx

  # Add Orderly Key with specific chain
  node addOrderlyKey.js --wallet-id wal_xxx --chain-id 80001

Note:
  - The script generates an ed25519 key pair for Orderly authentication
  - The Orderly Key and Private Key will be saved to your .env file
  - Make sure your wallet has been registered with Orderly first (use registerOrderlyAccount.js)
        `);
        process.exit(0);
      }
    }

    const result = await addOrderlyKey(options);

    console.log("\n📝 Summary:");
    console.log(`   Wallet Address: ${result.userAddress}`);
    console.log(`   Orderly Key: ${result.orderlyKey}`);
    console.log(`   Orderly Private Key: ${result.orderlyPrivateKeyHex}`);

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to add Orderly Key");
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { addOrderlyKey, generateOrderlyKey };
