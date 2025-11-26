require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");

// Import all the script functions
const { createAgenticWallet } = require("./createAgenticWallet");
const { registerOrderlyAccount } = require("./registerOrderlyAccount");
const { addOrderlyKey } = require("./addOrderlyKey");
const { depositUSDC } = require("./depositUSDC");
const { createOrder } = require("./createOrder");
const { cancelOrder } = require("./cancelOrder");
const { withdrawFunds } = require("./withdrawUSDC");
const { getHolding } = require("./getHolding");
const { getOrders } = require("./getOrders");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// API Routes

// 1. Create Agentic Wallet
app.post("/api/create-wallet", async (req, res) => {
  try {
    const { policyId, chainType, name } = req.body;
    const wallet = await createAgenticWallet({ policyId, chainType, name });
    res.json({ success: true, data: wallet });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 2. Register Orderly Account
app.post("/api/register-orderly", async (req, res) => {
  try {
    const { walletId, walletAddress, chainId } = req.body;
    const result = await registerOrderlyAccount({
      walletId,
      walletAddress,
      chainId,
    });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 3. Add Orderly Key
app.post("/api/add-orderly-key", async (req, res) => {
  try {
    const { walletId, walletAddress, chainId } = req.body;
    const result = await addOrderlyKey({ walletId, walletAddress, chainId });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 4. Deposit USDC
app.post("/api/deposit-usdc", async (req, res) => {
  try {
    const { walletId, walletAddress, amount, chainId } = req.body;
    const result = await depositUSDC({
      walletId,
      walletAddress,
      amount,
      chainId,
    });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 5. Get Holding
app.post("/api/get-holding", async (req, res) => {
  try {
    const { walletId, walletAddress, all } = req.body;
    const result = await getHolding({ walletId, walletAddress, all });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 6. Create Order
app.post("/api/create-order", async (req, res) => {
  try {
    const {
      walletId,
      walletAddress,
      symbol,
      orderType,
      side,
      orderPrice,
      orderQuantity,
      orderAmount,
      visibleQuantity,
      reduceOnly,
      slippage,
      clientOrderId,
      orderTag,
      level,
      postOnlyAdjust,
    } = req.body;
    const result = await createOrder({
      walletId,
      walletAddress,
      symbol,
      orderType,
      side,
      orderPrice,
      orderQuantity,
      orderAmount,
      visibleQuantity,
      reduceOnly,
      slippage,
      clientOrderId,
      orderTag,
      level,
      postOnlyAdjust,
    });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 7. Get Orders
app.post("/api/get-orders", async (req, res) => {
  try {
    const {
      walletId,
      walletAddress,
      symbol,
      side,
      orderType,
      status,
      orderTag,
      startTime,
      endTime,
      page,
      size,
      sortBy,
    } = req.body;
    const result = await getOrders({
      walletId,
      walletAddress,
      symbol,
      side,
      orderType,
      status,
      orderTag,
      startTime,
      endTime,
      page,
      size,
      sortBy,
    });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 8. Cancel Order
app.post("/api/cancel-order", async (req, res) => {
  try {
    const { walletId, walletAddress, orderId, symbol } = req.body;
    const result = await cancelOrder({
      walletId,
      walletAddress,
      orderId,
      symbol,
    });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 9. Withdraw USDC
app.post("/api/withdraw-usdc", async (req, res) => {
  try {
    const { walletId, walletAddress, amount, token, chainId } = req.body;
    const result = await withdrawFunds({
      walletId,
      walletAddress,
      amount,
      token,
      chainId,
    });
    res.json({ success: true, data: result });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Health check
app.get("/api/health", (req, res) => {
  res.json({ success: true, message: "Server is running" });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(
    `📝 Make sure your .env file is configured with all required credentials`
  );
});
