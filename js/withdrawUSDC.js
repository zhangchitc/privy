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
const CHAIN_ID = process.env.CHAIN_ID ? parseInt(process.env.CHAIN_ID) : 80001; // Default: Polygon Mumbai testnet
const BROKER_ID = "woofi_pro";

// Verifying contract for withdrawals (different from other operations)
// Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/create-withdraw-request
const WITHDRAW_VERIFYING_CONTRACT =
  "0x6F7a338F2aA472838dEFD3283eB360d4Dff5D203";

// Token decimals mapping (common tokens)
// Most stablecoins like USDC, USDT use 6 decimals
const TOKEN_DECIMALS = {
  USDC: 6,
  USDT: 6,
  DAI: 18,
  WETH: 18,
  ETH: 18,
};

/**
 * Get withdrawal nonce from Orderly API
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/restful-api/private/get-withdrawal-nonce
 *
 * @param {string} accountId - Orderly account ID from environment variable
 * @param {string} orderlyKey - Orderly public key (ed25519:...)
 * @param {Uint8Array} orderlyPrivateKey - Orderly private key (32 bytes)
 * @returns {Promise<number>} - Withdrawal nonce
 */
async function getWithdrawalNonce(accountId, orderlyKey, orderlyPrivateKey) {
  try {
    const path = "/v1/withdraw_nonce";
    const requestConfig = await createAuthenticatedRequest(
      "GET",
      path,
      null,
      accountId,
      orderlyKey,
      orderlyPrivateKey
    );

    const response = await fetch(`${ORDERLY_API_URL}${path}`, requestConfig);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        `Failed to get withdrawal nonce: ${JSON.stringify(data)}`
      );
    }

    console.log("Withdrawal nonce response:", JSON.stringify(data, null, 2));

    // Extract nonce from response (adjust based on actual API response structure)
    return (
      data.data?.withdraw_nonce ||
      data.data?.nonce ||
      data.withdrawNonce ||
      data.nonce
    );
  } catch (error) {
    console.error("Error getting withdrawal nonce:", error);
    throw error;
  }
}

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
 * Withdraw funds from Orderly account using Privy agentic wallet
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/user-flows/withdrawal-deposit
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {string} options.amount - Amount to withdraw (in human-readable format, e.g., "100")
 * @param {string} options.token - Token symbol to withdraw (default: "USDC")
 * @param {number} options.chainId - Chain ID to withdraw to (optional, defaults to CHAIN_ID)
 * @returns {Promise<Object>} - Withdrawal result
 */
async function withdrawFunds(options = {}) {
  try {
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

    if (!options.amount) {
      throw new Error("Amount is required. Use --amount <amount>");
    }

    // Get Orderly credentials
    const orderlyKey = process.env.ORDERLY_KEY;
    if (!orderlyKey) {
      throw new Error(
        "ORDERLY_KEY environment variable is required for withdrawal (should be in format 'ed25519:...')"
      );
    }

    const orderlyPrivateKeyHex = process.env.ORDERLY_PRIVATE_KEY;
    if (!orderlyPrivateKeyHex) {
      throw new Error(
        "ORDERLY_PRIVATE_KEY environment variable is required for withdrawal (ed25519 private key in hex format)"
      );
    }

    // Convert hex string to Uint8Array
    const orderlyPrivateKey = hexToPrivateKey(orderlyPrivateKeyHex);

    // Initialize Privy client
    const privy = new PrivyClient({
      appId: appId,
      appSecret: appSecret,
    });

    // Create authorization context with the authorization private key
    const authorizationContext = {
      authorization_private_keys: [authorizationSecret],
    };

    // Configuration
    const chainId = options.chainId || CHAIN_ID;
    const chainIdNumber = parseInt(chainId, 10);
    const chainIdHex = `0x${BigInt(chainId).toString(16)}`;
    const brokerId = BROKER_ID;
    const token = (options.token || "USDC").toUpperCase();
    const amount = options.amount;

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

    console.log("\nPreparing withdrawal from Orderly...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Amount: ${amount} ${token}`);
    console.log(`   Chain ID: ${chainIdNumber} (${chainIdHex})`);
    console.log(`   Broker ID: ${brokerId}`);
    console.log(`   Account ID: ${accountId}`);

    // Step 1: Get withdrawal nonce
    console.log("\nStep 1: Fetching withdrawal nonce...");
    const withdrawNonce = await getWithdrawalNonce(
      accountId,
      orderlyKey,
      orderlyPrivateKey
    );
    console.log(`   Withdrawal nonce: ${withdrawNonce}`);

    // Step 2: Convert amount to smallest unit (uint256)
    const tokenDecimals = TOKEN_DECIMALS[token] || 18; // Default to 18 if not found
    console.log(`\nStep 2: Converting amount...`);
    console.log(`   Token: ${token}, Decimals: ${tokenDecimals}`);
    const amountInSmallestUnit = ethers.parseUnits(amount, tokenDecimals);
    console.log(
      `   Amount: ${amount} ${token} = ${amountInSmallestUnit.toString()} (smallest unit)`
    );

    // Step 3: Create EIP-712 message for withdrawal
    const timestamp = Date.now();
    const message = {
      brokerId: brokerId,
      chainId: chainIdNumber,
      receiver: walletAddress,
      token: token,
      amount: amountInSmallestUnit.toString(), // uint256 - as string
      withdrawNonce: withdrawNonce.toString(), // uint64 - as string
      timestamp: timestamp.toString(), // uint64 - as string
    };

    console.log("\nStep 3: Creating EIP-712 message...");
    console.log("Message:", JSON.stringify(message, null, 2));

    // Step 4: Create EIP-712 domain
    const domain = {
      name: "Orderly",
      version: "1",
      chainId: chainIdHex,
      verifyingContract: WITHDRAW_VERIFYING_CONTRACT,
    };

    // Step 5: Create EIP-712 types
    const typedData = {
      domain: domain,
      message: message,
      primary_type: "Withdraw",
      types: {
        EIP712Domain: [
          { name: "name", type: "string" },
          { name: "version", type: "string" },
          { name: "chainId", type: "uint256" },
          { name: "verifyingContract", type: "address" },
        ],
        Withdraw: [
          { name: "brokerId", type: "string" },
          { name: "chainId", type: "uint256" },
          { name: "receiver", type: "address" },
          { name: "token", type: "string" },
          { name: "amount", type: "uint256" },
          { name: "withdrawNonce", type: "uint64" },
          { name: "timestamp", type: "uint64" },
        ],
      },
    };

    // Step 6: Sign the EIP-712 message using Privy
    console.log("\nStep 4: Signing EIP-712 message...");
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

    // Step 7: Create withdraw request with Orderly authentication headers
    console.log("\nStep 5: Creating withdrawal request...");
    const path = "/v1/withdraw_request";

    // For API request body, convert numeric values to strings as per API documentation
    const requestBody = {
      message: {
        brokerId: message.brokerId,
        chainId: message.chainId,
        receiver: message.receiver,
        token: message.token,
        amount: message.amount.toString(), // Convert BigInt to string for JSON
        withdrawNonce: message.withdrawNonce.toString(), // Convert to string for JSON
        timestamp: message.timestamp.toString(), // Convert to string for JSON
      },
      signature: signature,
      userAddress: walletAddress,
      verifyingContract: WITHDRAW_VERIFYING_CONTRACT, // Required field according to API docs
    };

    console.log("Request body:", JSON.stringify(requestBody, null, 2));

    const requestConfig = await createAuthenticatedRequest(
      "POST",
      path,
      requestBody,
      accountId,
      orderlyKey,
      orderlyPrivateKey
    );

    const withdrawResponse = await fetch(
      `${ORDERLY_API_URL}${path}`,
      requestConfig
    );

    const withdrawData = await withdrawResponse.json();

    // Check both HTTP status and success field in response body
    if (!withdrawResponse.ok) {
      throw new Error(
        `Withdrawal request failed: ${JSON.stringify(withdrawData)}`
      );
    }

    // Orderly API returns success: false in body even with 200 status
    if (!withdrawData.success) {
      throw new Error(
        `Withdrawal request failed: ${JSON.stringify(withdrawData)}`
      );
    }

    console.log("\n✅ Withdrawal request successful!");
    console.log("Response:", JSON.stringify(withdrawData, null, 2));

    return {
      success: true,
      data: withdrawData,
      userAddress: walletAddress,
      amount: amount,
      token: token,
      targetChainId: chainIdNumber,
      withdrawNonce: withdrawNonce,
    };
  } catch (error) {
    console.error("\n❌ Failed to withdraw funds");
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
      } else if (args[i] === "--amount" && args[i + 1]) {
        options.amount = args[i + 1];
        i++;
      } else if (args[i] === "--token" && args[i + 1]) {
        options.token = args[i + 1];
        i++;
      } else if (args[i] === "--chain-id" && args[i + 1]) {
        options.chainId = args[i + 1];
        i++;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node withdrawUSDC.js [options]

Options:
  --wallet-id <id>        Privy wallet ID to use (required)
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --amount <amount>       Amount to withdraw (required, e.g., "100")
  --token <token>         Token symbol to withdraw (optional, default: "USDC")
  --chain-id <id>         Chain ID (optional, default: 80001 = Polygon Mumbai)
  --help, -h              Show this help message

Examples:
  # Withdraw 100 USDC on Polygon Mumbai
  node withdrawUSDC.js --wallet-id wal_xxx --amount 100

  # Withdraw with specific chain
  node withdrawUSDC.js --wallet-id wal_xxx --amount 50 --chain-id 421614

Environment Variables:
  PRIVY_APP_ID              Privy App ID (required)
  PRIVY_APP_SECRET          Privy App Secret (required)
  PRIVY_AUTHORIZATION_ID    Privy Authorization ID (required)
  PRIVY_AUTHORIZATION_SECRET Privy Authorization Secret (required)
  ORDERLY_KEY               Orderly public key (ed25519:...) (required)
  ORDERLY_PRIVATE_KEY       Orderly private key in hex format (required)

Note: Orderly account ID is automatically derived from wallet address and broker ID.
        `);
        process.exit(0);
      }
    }

    // Validate minimum withdrawal amount
    if (options.amount) {
      const amountNum = parseFloat(options.amount);
      if (isNaN(amountNum) || amountNum < 1.001) {
        console.error(
          `Error: Withdrawal amount must be at least 1.001. Got: ${options.amount}`
        );
        process.exit(1);
      }
    }

    const result = await withdrawFunds(options);

    console.log("\n📝 Withdrawal Summary:");
    console.log(`   Wallet Address: ${result.userAddress}`);
    console.log(`   Amount: ${result.amount} ${result.token}`);
    console.log(`   Target Chain ID: ${result.targetChainId}`);
    console.log(`   Withdrawal Nonce: ${result.withdrawNonce}`);
    console.log("\nNote: The withdrawal will be processed by Orderly Network.");
    console.log(
      "Check your wallet on the target chain after processing completes."
    );

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to withdraw funds:", error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { withdrawFunds, getWithdrawalNonce };
