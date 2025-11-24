const { sign } = require("@noble/ed25519");
const bs58 = require("bs58");

// Use webcrypto if available for @noble/ed25519
if (typeof globalThis !== "undefined" && !globalThis.crypto) {
  const { webcrypto } = require("node:crypto");
  globalThis.crypto = webcrypto;
}

/**
 * Convert hex string to Uint8Array private key
 * @param {string} hexKey - Private key in hex format
 * @returns {Uint8Array} - Private key as Uint8Array
 */
function hexToPrivateKey(hexKey) {
  // Remove '0x' prefix if present
  const cleanHex = hexKey.startsWith("0x") ? hexKey.slice(2) : hexKey;
  return Buffer.from(cleanHex, "hex");
}

/**
 * Create authenticated request configuration for Orderly API
 * Based on Orderly documentation: https://orderly.network/docs/build-on-omnichain/evm-api/api-authentication
 *
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {string} path - API path (e.g., "/v1/withdraw_nonce")
 * @param {Object|null} body - Request body (null for GET requests)
 * @param {string} accountId - Orderly account ID
 * @param {string} orderlyKey - Orderly public key (ed25519:...)
 * @param {Uint8Array} orderlyPrivateKey - Orderly private key (32 bytes)
 * @returns {Promise<Object>} - Request configuration with headers
 */
async function createAuthenticatedRequest(
  method,
  path,
  body,
  accountId,
  orderlyKey,
  orderlyPrivateKey
) {
  const timestamp = Date.now().toString();
  const message =
    timestamp + method + path + (body ? JSON.stringify(body) : "");

  // Sign the message with ed25519 private key
  const messageBytes = Buffer.from(message, "utf-8");
  const signature = await sign(messageBytes, orderlyPrivateKey);

  // Encode signature to base64
  const signatureBase64 = Buffer.from(signature).toString("base64");

  // Extract the public key part from orderlyKey (remove "ed25519:" prefix)
  const publicKeyPart = orderlyKey.replace("ed25519:", "");

  // Create headers
  const headers = {
    "Content-Type": "application/json",
    "orderly-timestamp": timestamp,
    "orderly-account-id": accountId,
    "orderly-key": orderlyKey,
    "orderly-signature": signatureBase64,
  };

  return {
    method: method,
    headers: headers,
    body: body ? JSON.stringify(body) : undefined,
  };
}

module.exports = {
  createAuthenticatedRequest,
  hexToPrivateKey,
};
