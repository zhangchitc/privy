"""
Flask server that exposes API endpoints for all Privy/Orderly operations
"""
import os
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from create_agentic_wallet import create_agentic_wallet
from register_orderly_account import register_orderly_account
from add_orderly_key import add_orderly_key
from deposit_usdc import deposit_usdc
from get_holding import get_holding
from get_positions import get_positions
from create_order import create_order
from get_orders import get_orders
from cancel_order import cancel_order
from cancel_all_orders import cancel_all_orders
from close_all_positions import close_all_positions
from settle_pnl import settle_pnl
from withdraw_usdc import withdraw_funds

load_dotenv()

app = Flask(__name__)
CORS(app)

# Authentication
def require_api_key(f):
    """
    Decorator to require API key authentication for protected endpoints.
    Expects API key in X-API-Key header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.environ.get("API_KEY")
        
        # If no API_KEY is set, skip authentication (for development)
        if not api_key:
            return f(*args, **kwargs)
        
        # Get API key from request header
        provided_key = request.headers.get("X-API-Key")
        
        if not provided_key:
            return jsonify({
                "success": False,
                "error": "Missing API key. Please provide X-API-Key header."
            }), 401
        
        if provided_key != api_key:
            return jsonify({
                "success": False,
                "error": "Invalid API key."
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


# Root endpoint
@app.route("/")
def index():
    return jsonify({
        "message": "Privy Orderly API Server",
        "status": "running",
        "endpoints": "/api/health"
    })


# API Routes

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"success": True, "message": "Server is running"})


@app.route("/api/create-wallet", methods=["POST"])
@require_api_key
def api_create_wallet():
    try:
        data = request.json or {}
        wallet = create_agentic_wallet(
            policy_id=data.get("policyId"),
            chain_type=data.get("chainType", "ethereum")
        )
        return jsonify({"success": True, "data": wallet})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/register-orderly", methods=["POST"])
@require_api_key
def api_register_orderly():
    try:
        data = request.json or {}
        result = register_orderly_account(
            wallet_id=data.get("walletId"),
            chain_id=data.get("chainId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/add-orderly-key", methods=["POST"])
@require_api_key
def api_add_orderly_key():
    try:
        data = request.json or {}
        result = add_orderly_key(
            wallet_id=data.get("walletId"),
            chain_id=data.get("chainId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/prepare-orderly-account", methods=["POST"])
@require_api_key
def api_prepare_orderly_account():
    """
    Complete wallet setup: creates wallet, registers Orderly account, and adds Orderly key
    """
    try:
        data = request.json or {}
        
        # Step 1: Create agentic wallet
        wallet = create_agentic_wallet(
            policy_id=data.get("policyId"),
            chain_type=data.get("chainType", "ethereum")
        )
        
        # Extract wallet ID from the result
        wallet_id = wallet.get("id") or wallet.get("wallet_id")
        if not wallet_id:
            raise ValueError("Failed to get wallet ID from wallet creation response")
        
        # Step 2: Register Orderly account
        register_result = register_orderly_account(
            wallet_id=wallet_id,
            chain_id=data.get("chainId", "421614")
        )
        
        # Step 3: Add Orderly key
        # Use chain_id from request or default from add_orderly_key function
        add_key_result = add_orderly_key(
            wallet_id=wallet_id,
            chain_id=int(data.get("chainId"))
        )
        
        return jsonify({
            "success": True,
            "data": {
                "walletId": wallet_id,
                "walletAddress": wallet.get("address"),
                "orderlyAccountId": register_result.get("orderlyAccountId"),
            }
        })
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/deposit-usdc", methods=["POST"])
@require_api_key
def api_deposit_usdc():
    try:
        data = request.json or {}
        result = deposit_usdc(
            wallet_id=data.get("walletId"),
            amount=data.get("amount"),
            chain_id=data.get("chainId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/get-holding", methods=["POST"])
@require_api_key
def api_get_holding():
    try:
        data = request.json or {}
        result = get_holding(
            wallet_id=data.get("walletId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/get-positions", methods=["POST"])
@require_api_key
def api_get_positions():
    try:
        data = request.json or {}
        result = get_positions(
            wallet_id=data.get("walletId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/create-order", methods=["POST"])
@require_api_key
def api_create_order():
    try:
        data = request.json or {}
        result = create_order(
            wallet_id=data.get("walletId"),
            symbol=data.get("symbol"),
            order_type=data.get("orderType"),
            side=data.get("side"),
            order_price=data.get("orderPrice"),
            order_quantity=data.get("orderQuantity"),
            order_amount=data.get("orderAmount"),
            visible_quantity=data.get("visibleQuantity"),
            reduce_only=data.get("reduceOnly"),
            slippage=data.get("slippage"),
            client_order_id=data.get("clientOrderId"),
            order_tag=data.get("orderTag"),
            level=data.get("level"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/get-orders", methods=["POST"])
@require_api_key
def api_get_orders():
    try:
        data = request.json or {}
        result = get_orders(
            wallet_id=data.get("walletId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("orderType"),
            status=data.get("status"),
            order_tag=data.get("orderTag"),
            start_time=data.get("startTime"),
            end_time=data.get("endTime"),
            page=data.get("page"),
            size=data.get("size"),
            sort_by=data.get("sortBy"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/cancel-order", methods=["POST"])
@require_api_key
def api_cancel_order():
    try:
        data = request.json or {}
        result = cancel_order(
            wallet_id=data.get("walletId"),
            order_id=data.get("orderId"),
            symbol=data.get("symbol")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/cancel-all-orders", methods=["POST"])
@require_api_key
def api_cancel_all_orders():
    try:
        data = request.json or {}
        result = cancel_all_orders(
            wallet_id=data.get("walletId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/close-all-positions", methods=["POST"])
@require_api_key
def api_close_all_positions():
    try:
        data = request.json or {}
        result = close_all_positions(
            wallet_id=data.get("walletId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/settle-pnl", methods=["POST"])
@require_api_key
def api_settle_pnl():
    try:
        data = request.json or {}
        result = settle_pnl(
            wallet_id=data.get("walletId"),
            chain_id=data.get("chainId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/withdraw-usdc", methods=["POST"])
@require_api_key
def api_withdraw_usdc():
    try:
        data = request.json or {}
        result = withdraw_funds(
            wallet_id=data.get("walletId"),
            amount=data.get("amount"),
            token=data.get("token", "USDC"),
            chain_id=data.get("chainId")
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    # Disable debug mode in production (Heroku sets this automatically)
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    if not debug:
        print(f"🚀 Server running on port {port}")
    else:
        print(f"🚀 Server running on http://localhost:{port}")
        print("📝 Make sure your .env file is configured with all required credentials")
    
    app.run(host="0.0.0.0", port=port, debug=debug)

