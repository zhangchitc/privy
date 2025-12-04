"""
Flask server that exposes API endpoints for all Privy/Orderly operations
"""
import os
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
from withdraw_usdc import withdraw_funds

load_dotenv()

app = Flask(__name__)
CORS(app)

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


@app.route("/api/deposit-usdc", methods=["POST"])
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
            post_only_adjust=data.get("postOnlyAdjust"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/get-orders", methods=["POST"])
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


@app.route("/api/withdraw-usdc", methods=["POST"])
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

