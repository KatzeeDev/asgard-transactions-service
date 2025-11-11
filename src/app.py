"""
Asgard Transactions API
"""

from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

from flask import Flask, request, jsonify
from services import (
    create_transaction,
    get_transaction,
    list_transactions,
    ValidationError,
)

# logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ge transactions, all of them
@app.route("/transactions", methods=["GET"])
def list_transactions_endpoint():
    """
    endpoint to get all transactions
    example: GET /transactions
    """
    try:
        result = list_transactions()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing transactions: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# create a type of transacition
@app.route("/transactions", methods=["POST"])
def create_transaction_endpoint():
    """
    endpoint to create a new transaction

    expected JSON body:
    {
        "type": "AUTH|CAPTURE|REFUND",
        "amount": float,
        "currency": "CLP|USD|EUR",
        "merchant_id": str,
        "order_reference": str,
        "parent_transaction_id": str (optional, required for CAPTURE/REFUND),
        "metadata": {} (optional)
    }
    """
    # validations
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # required fields
    required = ["type", "amount", "currency", "merchant_id", "order_reference"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # extract
    transaction_type = data["type"]
    amount = data["amount"]
    currency = data["currency"]
    merchant_id = data["merchant_id"]
    order_reference = data["order_reference"]
    parent_transaction_id = data.get("parent_transaction_id")
    metadata = data.get("metadata")

    try:
        # delegate all business logic to services.py
        result = create_transaction(
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            merchant_id=merchant_id,
            order_reference=order_reference,
            parent_transaction_id=parent_transaction_id,
            metadata=metadata,
        )

        # format response based on whether it's duplicate or new
        if result["is_duplicate"]:
            return (
                jsonify(
                    {
                        "message": "Transaction already exists",
                        "transaction_id": result["transaction_id"],
                        "status": result["status"],
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "message": "Transaction created successfully",
                        "transaction_id": result["transaction_id"],
                        "status": result["status"],
                    }
                ),
                201,
            )

    except ValidationError as e:
        # business validation error
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # unexpected error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# transaction by id
@app.route("/transactions/<transaction_id>", methods=["GET"])
def get_transaction_endpoint(transaction_id):
    """
    endpoint to get a single transaction by ID
    example: GET /transactions/TXN_20250110_143052_AUTH_a3f9k2p8
    """
    try:
        transaction = get_transaction(transaction_id)

        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        return jsonify(transaction), 200

    except Exception as e:
        logger.error(f"Error retrieving transaction: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"Starting Asgard API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
