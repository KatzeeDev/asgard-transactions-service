"""
Asgard Transactions API
"""

from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

from flask import Flask, request, jsonify
from db import get_transaction_by_order, get_transaction_by_id, insert_transaction
from utils import generate_transaction_id

# logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
ALLOWED_CURRENCIES = ("CLP", "USD", "EUR")
ALLOWED_TRANSACTION_TYPES = ("AUTH", "CAPTURE", "REFUND")

app = Flask(__name__)


@app.route("/transactions", methods=["POST"])
def create_transaction():
    """Create a new transaction"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # required fields
    required = ["type", "amount", "currency", "merchant_id", "order_reference"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # some fields
    transaction_type = data["type"]
    amount = data["amount"]
    currency = data["currency"]
    merchant_id = data["merchant_id"]
    order_reference = data["order_reference"]
    parent_transaction_id = data.get("parent_transaction_id")
    metadata = data.get("metadata")

    try:
        # check if transaction already exists -> idempotency
        existing = get_transaction_by_order(merchant_id, order_reference)
        if existing:
            logger.info(f"Transaction already exists: {existing['transaction_id']}")
            return (
                jsonify(
                    {
                        "message": "Transaction already exists",
                        "transaction_id": existing["transaction_id"],
                        "status": existing["status"],
                    }
                ),
                200,
            )

        # validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({"error": "Amount must be greater than zero"}), 400
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid amount"}), 400

        # validate some currency
        if currency not in ALLOWED_CURRENCIES:
            return jsonify({"error": f"Currency must be one of {', '.join(ALLOWED_CURRENCIES)}"}), 400

        # validate transaction type
        if transaction_type not in ALLOWED_TRANSACTION_TYPES:
            return jsonify({"error": f"Type must be one of {', '.join(ALLOWED_TRANSACTION_TYPES)}"}), 400

        # first try to create some bussines rule: CAPTURE and REFUND need parent_transaction_id
        if transaction_type in ("CAPTURE", "REFUND"):
            if not parent_transaction_id:
                return (
                    jsonify(
                        {"error": f"{transaction_type} requires parent_transaction_id"}
                    ),
                    400,
                )

            # verify if parent exists
            parent = get_transaction_by_id(parent_transaction_id)
            if not parent:
                return jsonify({"error": "Parent transaction not found"}), 400

            # validate parent type
            if transaction_type == "CAPTURE" and parent["type"] != "AUTH":
                return jsonify({"error": "CAPTURE must reference an AUTH"}), 400

            if transaction_type == "REFUND" and parent["type"] not in (
                "AUTH",
                "CAPTURE",
            ):
                return jsonify({"error": "REFUND must reference AUTH or CAPTURE"}), 400

        # some bussines rule: AUTH should not have parent
        if transaction_type == "AUTH" and parent_transaction_id:
            return jsonify({"error": "AUTH cannot have parent_transaction_id"}), 400

        #  metadata if provided
        if metadata and not isinstance(metadata, dict):
            return jsonify({"error": "metadata must be a JSON object"}), 400

        # generate transaction ID
        transaction_id = generate_transaction_id(transaction_type)

        # insert into database
        insert_transaction(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            merchant_id=merchant_id,
            order_reference=order_reference,
            parent_transaction_id=parent_transaction_id,
            metadata=metadata,
            status="PENDING",
        )

        logger.info(f"Transaction created: {transaction_id}")

        return (
            jsonify(
                {
                    "message": "Transaction created successfully",
                    "transaction_id": transaction_id,
                    "status": "PENDING",
                }
            ),
            201,
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
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
