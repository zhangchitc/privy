require("dotenv").config();
const { PrivyClient } = require("@privy-io/node");
const { ethers } = require("ethers");
const { keccak256 } = require("ethers");

// Configuration
const ORDERLY_API_URL = "https://api.orderly.org"; // or https://testnet-api.orderly.org for testnet
const CHAIN_ID = process.env.CHAIN_ID ? parseInt(process.env.CHAIN_ID) : 80001; // Default: Polygon Mumbai testnet
const BROKER_ID = "woofi_pro";

// USDC token addresses from Orderly documentation
// Source: https://orderly.network/docs/build-on-omnichain/addresses
const USDC_ADDRESSES = {
  // Ethereum
  1: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", // Ethereum Mainnet
  11155111: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238", // Ethereum Sepolia (Testnet)
  // Arbitrum
  42161: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", // Arbitrum One (Mainnet)
  421614: "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d", // Arbitrum Sepolia (Testnet)
  // Optimism
  10: "0x0b2c639c533813f4aa9d7837caf62653d097ff85", // Optimism Mainnet
  11155420: "0x5fd84259d66Cd46123540766Be93DFE6D43130D7", // Optimism Sepolia (Testnet)
  // Base
  8453: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", // Base Mainnet
  84532: "0x036CbD53842c5426634e7929541eC2318f3dCF7e", // Base Sepolia (Testnet)
  // Mantle
  5000: "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9", // Mantle Mainnet (USDC.e)
  5003: "0xAcab8129E2cE587fD203FD770ec9ECAFA2C88080", // Mantle Sepolia (Testnet)
  // BNB Smart Chain
  56: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", // BNB Smart Chain Mainnet
  97: "0x31873b5804bABE258d6ea008f55e08DD00b7d51E", // BNB Smart Chain Testnet
  // Polygon
  137: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", // Polygon Mainnet
  80001: "0x41e94eb019c0762f9bfcf9fb1f3f082b1e1e2079", // Polygon Mumbai (Testnet)
};

// Standard ERC20 ABI for transfer function
const ERC20_ABI = [
  "function transfer(address to, uint256 amount) external returns (bool)",
  "function approve(address spender, uint256 amount) external returns (bool)",
  "function balanceOf(address account) external view returns (uint256)",
  "function decimals() external view returns (uint8)",
  "function allowance(address owner, address spender) external view returns (uint256)",
];

// Orderly Vault contract addresses from Orderly documentation
// Source: https://orderly.network/docs/build-on-omnichain/addresses
const ORDERLY_VAULT = {
  // Ethereum
  1: "0x816f722424b49cf1275cc86da9840fbd5a6167e9", // Ethereum Mainnet
  11155111: "0x0EaC556c0C2321BA25b9DC01e4e3c95aD5CDCd2f", // Ethereum Sepolia (Testnet)
  // Arbitrum
  42161: "0x816f722424B49Cf1275cc86DA9840Fbd5a6167e9", // Arbitrum One (Mainnet)
  421614: "0x0EaC556c0C2321BA25b9DC01e4e3c95aD5CDCd2f", // Arbitrum Sepolia (Testnet)
  // Optimism
  10: "0x816f722424b49cf1275cc86da9840fbd5a6167e9", // Optimism Mainnet
  11155420: "0xEfF2896077B6ff95379EfA89Ff903598190805EC", // Optimism Sepolia (Testnet)
  // Base
  8453: "0x816f722424b49cf1275cc86da9840fbd5a6167e9", // Base Mainnet
  84532: "0xdc7348975aE9334DbdcB944DDa9163Ba8406a0ec", // Base Sepolia (Testnet)
  // Mantle
  5000: "0x816f722424b49cf1275cc86da9840fbd5a6167e9", // Mantle Mainnet
  5003: "0xfb0E5f3D16758984E668A3d76f0963710E775503", // Mantle Sepolia (Testnet)
  // BNB Smart Chain
  56: "0x816f722424B49Cf1275cc86DA9840Fbd5a6167e9", // BNB Smart Chain Mainnet
  97: "0xaf2036D5143219fa00dDd90e7A2dbF3E36dba050", // BNB Smart Chain Testnet
  // Polygon
  137: "0x816f722424b49cf1275cc86da9840fbd5a6167e9", // Polygon Mainnet
  80001: "0x816f722424b49cf1275cc86da9840fbd5a6167e9", // Polygon Mumbai (Testnet)
};

// RPC URLs for supported chain IDs (update with your provider keys if necessary)
const RPC_URLS = {
  // Ethereum
  1: "https://rpc.ankr.com/eth",
  11155111: "https://rpc.ankr.com/eth_sepolia",
  // Arbitrum
  42161: "https://arb1.arbitrum.io/rpc",
  421614: "https://sepolia-rollup.arbitrum.io/rpc",
  // Optimism
  10: "https://mainnet.optimism.io",
  11155420: "https://sepolia.optimism.io",
  // Base
  8453: "https://mainnet.base.org",
  84532: "https://sepolia.base.org",
  // Mantle
  5000: "https://rpc.mantle.xyz",
  5003: "https://rpc.sepolia.mantle.xyz",
  // BNB Smart Chain
  56: "https://bsc-dataseed.binance.org/",
  97: "https://data-seed-prebsc-1-s1.binance.org:8545/",
  // Polygon
  137: "https://polygon-rpc.com",
  80001: "https://rpc.ankr.com/polygon_mumbai",
};

// Vault contract ABI (simplified - may need to be updated based on actual contract)
const VAULT_ABI = [
  "function deposit(tuple(bytes32 accountId, bytes32 brokerHash, bytes32 tokenHash, uint128 tokenAmount) depositData) external payable",
  "function getDepositFee(address account, tuple(bytes32 accountId, bytes32 brokerHash, bytes32 tokenHash, uint128 tokenAmount) depositData) external view returns (uint256)",
];

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
  return keccak256(
    abiCoder.encode(["address", "bytes32"], [address, brokerIdHash])
  );
}

/**
 * Deposit USDC to Orderly account using Privy agentic wallet
 * This involves:
 * 1. Approving USDC transfer to Orderly Vault (if needed)
 * 2. Calling the deposit function on the Orderly Vault contract
 *
 * @param {Object} options - Configuration options
 * @param {string} options.walletId - The Privy wallet ID (required)
 * @param {string} options.walletAddress - The wallet address (optional, will be fetched if not provided)
 * @param {string} options.amount - Amount of USDC to deposit (in human-readable format, e.g., "100")
 * @param {number} options.chainId - The chain ID (optional, defaults to CHAIN_ID)
 * @returns {Promise<Object>} - Deposit result
 */
async function depositUSDC(options = {}) {
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
  const amount = options.amount;

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

    console.log("\nPreparing USDC deposit to Orderly...");
    console.log(`   Wallet ID: ${options.walletId}`);
    console.log(`   Wallet Address: ${walletAddress}`);
    console.log(`   Amount: ${amount} USDC`);
    console.log(`   Chain ID: ${chainId} (${chainIdHex})`);
    console.log(`   Broker ID: ${brokerId}`);

    // Get USDC contract address for the chain
    const usdcAddress = USDC_ADDRESSES[chainIdNumber];
    if (!usdcAddress) {
      throw new Error(
        `USDC address not configured for chain ID ${chainIdNumber}. Please update USDC_ADDRESSES.`
      );
    }

    // Get Orderly Vault contract address
    const vaultAddress = ORDERLY_VAULT[chainIdNumber];
    if (!vaultAddress) {
      throw new Error(
        `Orderly Vault address not configured for chain ID ${chainIdNumber}. ` +
          `See https://orderly.network/docs/build-on-omnichain/addresses for addresses.`
      );
    }

    console.log(`   USDC Address: ${usdcAddress}`);
    console.log(`   Orderly Vault: ${vaultAddress}`);

    // Get RPC URL
    const rpcUrl = RPC_URLS[chainIdNumber];
    if (!rpcUrl) {
      throw new Error(
        `RPC URL not configured for chain ID ${chainIdNumber}. Please update RPC_URLS in the script.`
      );
    }

    // Create provider for reading contract state
    const provider = new ethers.JsonRpcProvider(rpcUrl);

    // Get USDC contract instance
    const usdcContract = new ethers.Contract(usdcAddress, ERC20_ABI, provider);

    // Get USDC decimals
    const decimals = await usdcContract.decimals();
    console.log(`   USDC decimals: ${decimals}`);

    // Convert amount to wei/smallest unit
    const amountWei = ethers.parseUnits(amount, decimals);
    console.log(`   Amount in smallest unit: ${amountWei.toString()}`);

    // Check balance
    const balance = await usdcContract.balanceOf(walletAddress);
    console.log(
      `   Current USDC balance: ${ethers.formatUnits(balance, decimals)}`
    );

    if (balance < amountWei) {
      throw new Error(
        `Insufficient balance. Required: ${amount}, Available: ${ethers.formatUnits(
          balance,
          decimals
        )}`
      );
    }

    // Check and approve USDC allowance if needed
    const currentAllowance = await usdcContract.allowance(
      walletAddress,
      vaultAddress
    );
    console.log(
      `   Current allowance: ${ethers.formatUnits(currentAllowance, decimals)}`
    );

    if (currentAllowance < amountWei) {
      console.log("\nApproving USDC transfer to Orderly Vault...");

      // Encode approve function call
      const iface = new ethers.Interface(ERC20_ABI);
      const approveData = iface.encodeFunctionData("approve", [
        vaultAddress,
        amountWei,
      ]);

      // Send approve transaction using Privy
      const approveResponse = await privy
        .wallets()
        .ethereum()
        .sendTransaction(options.walletId, {
          authorization_context: authorizationContext,
          caip2: `eip155:${chainIdNumber}`,
          params: {
            transaction: {
              chain_id: chainIdHex,
              to: usdcAddress,
              data: approveData,
            },
          },
        });

      console.log(
        `   Approval transaction hash: ${
          approveResponse.transaction_hash || approveResponse.hash
        }`
      );
      console.log("   Waiting for approval confirmation...");

      // Wait for transaction confirmation
      const approveReceipt = await provider.waitForTransaction(
        approveResponse.transaction_hash || approveResponse.hash
      );
      console.log(
        `   Approval confirmed in block: ${approveReceipt.blockNumber}`
      );

      // Verify allowance updated (poll up to 10 times with 1s delay)
      for (let i = 0; i < 10; i++) {
        const verifiedAllowance = await usdcContract.allowance(
          walletAddress,
          vaultAddress
        );
        if (verifiedAllowance >= amountWei) {
          console.log("   Allowance verified");
          break;
        }
        if (i === 9) {
          throw new Error(
            `Allowance verification failed. Expected: ${ethers.formatUnits(
              amountWei,
              decimals
            )}, Got: ${ethers.formatUnits(verifiedAllowance, decimals)}`
          );
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    } else {
      console.log("   Sufficient allowance already exists");
    }

    // Prepare deposit data
    const orderlyAccountId = getAccountId(walletAddress, brokerId);
    const encoder = new TextEncoder();
    const brokerHash = keccak256(encoder.encode(brokerId));
    const tokenHash = keccak256(encoder.encode("USDC"));

    // Convert amountWei to uint128 (truncate if necessary)
    const tokenAmount =
      BigInt(amountWei.toString()) &
      BigInt("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF");

    const depositData = {
      accountId: orderlyAccountId,
      brokerHash: brokerHash,
      tokenHash: tokenHash,
      tokenAmount: tokenAmount,
    };

    console.log("\nDeposit data prepared:");
    console.log(`   Account ID: ${orderlyAccountId}`);
    console.log(`   Broker Hash: ${brokerHash}`);
    console.log(`   Token Hash: ${tokenHash}`);
    console.log(`   Token Amount: ${tokenAmount.toString()}`);

    // Get deposit fee
    const vaultContract = new ethers.Contract(
      vaultAddress,
      VAULT_ABI,
      provider
    );

    console.log("\nCalculating deposit fee...");
    const depositFee = await vaultContract.getDepositFee(
      walletAddress,
      depositData
    );
    console.log(`   Deposit fee: ${ethers.formatEther(depositFee)} ETH`);

    // Encode deposit function call
    const vaultIface = new ethers.Interface(VAULT_ABI);
    const depositDataEncoded = vaultIface.encodeFunctionData("deposit", [
      depositData,
    ]);

    // Call deposit function on Orderly Vault contract
    console.log(`\nDepositing ${amount} USDC to Orderly Vault...`);
    const depositResponse = await privy
      .wallets()
      .ethereum()
      .sendTransaction(options.walletId, {
        authorization_context: authorizationContext,
        caip2: `eip155:${chainIdNumber}`,
        params: {
          transaction: {
            chain_id: chainIdHex,
            to: vaultAddress,
            data: depositDataEncoded,
            value: `0x${BigInt(depositFee.toString()).toString(16)}`, // Deposit fee in hex
          },
        },
      });

    const txHash = depositResponse.transaction_hash || depositResponse.hash;
    console.log(`   Transaction hash: ${txHash}`);
    console.log("   Waiting for transaction confirmation...");

    // Wait for transaction confirmation
    const receipt = await provider.waitForTransaction(txHash);
    console.log(`   Transaction confirmed in block: ${receipt.blockNumber}`);

    console.log("\n✅ USDC deposit successful!");

    return {
      success: true,
      transactionHash: txHash,
      blockNumber: receipt.blockNumber,
      vaultAddress: vaultAddress,
      amount: amount,
      token: "USDC",
      userAddress: walletAddress,
      orderlyAccountId: orderlyAccountId,
    };
  } catch (error) {
    console.error("\n❌ Failed to deposit USDC");
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
      } else if (args[i] === "--amount" && args[i + 1]) {
        options.amount = args[i + 1];
        i++;
      } else if (args[i] === "--chain-id" && args[i + 1]) {
        options.chainId = args[i + 1];
        i++;
      } else if (args[i] === "--help" || args[i] === "-h") {
        console.log(`
Usage: node depositUSDC.js [options]

Options:
  --wallet-id <id>        Privy wallet ID to use (required)
  --wallet-address <addr>  Wallet address (optional, will be fetched if not provided)
  --amount <amount>       Amount of USDC to deposit (required, e.g., "100")
  --chain-id <id>         Chain ID (optional, default: 80001 = Polygon Mumbai)
  --help, -h              Show this help message

Examples:
  # Deposit 100 USDC on Polygon Mumbai
  node depositUSDC.js --wallet-id wal_xxx --amount 100

  # Deposit with specific chain
  node depositUSDC.js --wallet-id wal_xxx --amount 50 --chain-id 421614

Supported Chains:
  - Polygon Mumbai: 80001 (testnet)
  - Arbitrum Sepolia: 421614 (testnet)
  - Ethereum Sepolia: 11155111 (testnet)
  - Base Sepolia: 84532 (testnet)
  - And other chains supported by Orderly (check their documentation)

Note:
  - Make sure your wallet has sufficient USDC balance
  - The script will automatically approve USDC transfer if needed
  - Deposit fee (in native token) will be included in the transaction
  - Make sure your wallet has been registered with Orderly first (use registerOrderlyAccount.js)
        `);
        process.exit(0);
      }
    }

    const result = await depositUSDC(options);

    console.log("\n📝 Deposit Summary:");
    console.log(`   Wallet Address: ${result.userAddress}`);
    console.log(`   Transaction Hash: ${result.transactionHash}`);
    console.log(`   Block Number: ${result.blockNumber}`);
    console.log(`   Amount: ${result.amount} ${result.token}`);
    console.log(`   Vault Address: ${result.vaultAddress}`);
    console.log(`   Orderly Account ID: ${result.orderlyAccountId}`);

    process.exit(0);
  } catch (error) {
    console.error("\n❌ Failed to deposit USDC");
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { depositUSDC, getAccountId };
