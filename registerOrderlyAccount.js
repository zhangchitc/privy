require("dotenv").config();
const { PrivyClient } = require("@privy-io/node");

/**
 * Registers an account on Orderly Network using a Privy agentic wallet
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The wallet ID to use for registration
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {string} options.chainId - Chain ID (optional, defaults to 421614 for Arbitrum Sepolia)
 * @returns {Promise<Object>} The registration response
 */
async function registerOrderlyAccount(options = {}) {
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

  // Default to Arbitrum Sepolia testnet (chain ID: 421614)
  // Orderly supports multiple chains - check their docs for mainnet chain IDs
  const chainId = options.chainId || "421614"; // Arbitrum Sepolia
  const chainIdNumber = parseInt(chainId, 10);
  const chainIdHex = `0x${BigInt(chainId).toString(16)}`;

  // Orderly API endpoints
  // Testnet: https://testnet-api.orderly.org
  // Mainnet: https://api.orderly.org
  const orderlyApiUrl = "https://api.orderly.org";

  // Broker ID - default to "woofi_dex", can be customized
  const brokerId = "woofi_pro";

  // Create authorization context with the authorization private key
  const authorizationContext = {
    authorization_private_keys: [authorizationSecret],
  };

  try {
    // Get wallet address if not provided
    let walletAddress = options.walletAddress;
    if (!walletAddress) {
      console.log("Fetching wallet details...");
      // Use the get() method to retrieve wallet by ID
      // Reference: https://docs.privy.io/wallets/wallets/get-a-wallet/get-wallet-by-id
      const wallet = await privy.wallets().get(options.walletId);

      if (!wallet) {
        throw new Error(`Wallet with ID ${options.walletId} not found`);
      }

      // Extract address from wallet object
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

    console.log("\nPreparing Orderly account registration...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Chain ID: ${chainId} (${chainIdHex})`);
    console.log(`   Broker ID: ${brokerId}`);
    console.log(`   Orderly API: ${orderlyApiUrl}`);

    // Step 1: Get registration nonce from Orderly
    // Reference: https://orderly.network/docs/build-on-omnichain/user-flows/accounts
    console.log("\nStep 1: Getting registration nonce...");
    const nonceResponse = await fetch(`${orderlyApiUrl}/v1/registration_nonce`);
    if (!nonceResponse.ok) {
      const errorText = await nonceResponse.text();
      throw new Error(
        `Failed to get registration nonce (${nonceResponse.status}): ${errorText}`
      );
    }
    const nonceData = await nonceResponse.json();
    const registrationNonce = nonceData.data.registration_nonce;
    console.log(`   Registration Nonce: ${registrationNonce}`);

    // Step 2: Prepare EIP-712 typed data for Orderly registration
    // Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/accounts
    const domain = {
      name: "Orderly",
      version: "1",
      chainId: chainIdHex, // Hex format for EIP-712
      verifyingContract: "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC",
    };

    // Message structure according to Orderly documentation
    const timestamp = Date.now(); // UNIX milliseconds
    const registerMessage = {
      brokerId: brokerId,
      chainId: chainIdNumber, // Number format for the message
      timestamp: timestamp,
      registrationNonce: registrationNonce,
    };

    // EIP-712 types structure
    const typedData = {
      domain: domain,
      message: registerMessage,
      primary_type: "Registration", // snake_case as required by Privy
      types: {
        EIP712Domain: [
          { name: "name", type: "string" },
          { name: "version", type: "string" },
          { name: "chainId", type: "uint256" },
          { name: "verifyingContract", type: "address" },
        ],
        Registration: [
          { name: "brokerId", type: "string" },
          { name: "chainId", type: "uint256" },
          { name: "timestamp", type: "uint64" },
          { name: "registrationNonce", type: "uint256" },
        ],
      },
    };

    console.log("\nStep 2: Signing EIP-712 message...");
    console.log("Register message:", JSON.stringify(registerMessage, null, 2));

    // Step 3: Sign the typed data using Privy
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

    // Step 4: Register with Orderly API
    // Endpoint: /v1/register_account
    // Reference: https://orderly.network/docs/build-on-omnichain/user-flows/accounts
    console.log("\nStep 3: Registering account with Orderly...");
    const registrationPayload = {
      message: registerMessage,
      signature: signature,
      userAddress: walletAddress,
    };

    console.log(
      "Registration payload:",
      JSON.stringify(registrationPayload, null, 2)
    );

    const response = await fetch(`${orderlyApiUrl}/v1/register_account`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(registrationPayload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Orderly API error (${response.status}): ${errorText}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(
        `Orderly registration failed: ${result.message || "Unknown error"}`
      );
    }

    const orderlyAccountId = result.data.account_id;
    console.log("\n✅ Account registered successfully with Orderly!");
    console.log("Registration response:", JSON.stringify(result, null, 2));
    console.log(`\n📝 Orderly Account ID: ${orderlyAccountId}`);

    return {
      signature,
      walletAddress,
      orderlyAccountId,
      registration: result,
    };
  } catch (error) {
    console.error("\n❌ Failed to register Orderly account");
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
Usage: node registerOrderlyAccount.js [options]

Options:
  --wallet-id <id>        Wallet ID to use for registration (required)
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --chain-id <id>         Chain ID (optional, default: 421614 = Arbitrum Sepolia)
  --help, -h              Show this help message

Examples:
  # Register account on Orderly
  node registerOrderlyAccount.js --wallet-id wal_xxx

  # Register with specific chain
  node registerOrderlyAccount.js --wallet-id wal_xxx --chain-id 421614

Supported Chains:
  - Arbitrum Sepolia: 421614 (testnet, recommended for testing)
  - Arbitrum One: 42161 (mainnet)
  - Other chains supported by Orderly (check their documentation)

Note: 
  - Make sure your wallet has been created using createAgenticWallet.js
  - The script will sign an EIP-712 message for account registration
  - Check Orderly's API documentation for the exact endpoint and payload structure
        `);
        process.exit(0);
      }
    }

    const result = await registerOrderlyAccount(options);

    console.log("\n📝 Registration Summary:");
    console.log(`   Wallet Address: ${result.walletAddress}`);
    console.log(`   Orderly Account ID: ${result.orderlyAccountId || "N/A"}`);

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to register Orderly account");
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { registerOrderlyAccount };
