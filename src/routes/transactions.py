"""
http endpoints for transaction operations handles request/response and delegates to service layer
"""

import logging
from flask import Blueprint, request, jsonify
from services.transaction_service import (
    create_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
    delete_transaction,
)
from exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

# blueprint for transaction routes
transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions", methods=["GET"])
def list_transactions_endpoint():
    """get all transactions"""
    try:
        result = list_transactions()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"error listing transactions: {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@transactions_bp.route("/transactions", methods=["POST"])
def create_transaction_endpoint():
    """
    create new transaction

    expected json body:
    {
        "type": "AUTH|CAPTURE|REFUND",
        "amount": float,
        "currency": "CLP|USD|EUR",
        "merchant_id": str,
        "order_reference": str,
        "parent_transaction_id": str (optional, required for capture/refund),
        "metadata": {} (optional),
        "error_code": str (optional),
        "error_message": str (optional),
        "location": str (optional)
    }
    """
    # validate json body exists
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid json"}), 400

    # check required fields
    required = ["type", "amount", "currency", "merchant_id", "order_reference"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # extract fields from request
    transaction_type = data["type"]
    amount = data["amount"]
    currency = data["currency"]
    merchant_id = data["merchant_id"]
    order_reference = data["order_reference"]
    parent_transaction_id = data.get("parent_transaction_id")
    metadata = data.get("metadata")
    error_code = data.get("error_code")
    error_message = data.get("error_message")
    location = data.get("location")

    try:
        # delegate to service layer
        result = create_transaction(
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            merchant_id=merchant_id,
            order_reference=order_reference,
            parent_transaction_id=parent_transaction_id,
            metadata=metadata,
            error_code=error_code,
            error_message=error_message,
            location=location,
        )

        # format response based on duplicate or new
        if result["is_duplicate"]:
            return (
                jsonify(
                    {
                        "message": "transaction already exists",
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
                        "message": "transaction created successfully",
                        "transaction_id": result["transaction_id"],
                        "status": result["status"],
                    }
                ),
                201,
            )

    except ValidationError as e:
        # business validation failed
        logger.warning(f"validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # unexpected error
        logger.error(f"unexpected error: {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@transactions_bp.route("/transactions/<transaction_id>", methods=["GET"])
def get_transaction_endpoint(transaction_id):
    """get single transaction by id"""
    try:
        transaction = get_transaction(transaction_id)

        if not transaction:
            return jsonify({"error": "transaction not found"}), 404

        return jsonify(transaction), 200

    except Exception as e:
        logger.error(f"error retrieving transaction: {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@transactions_bp.route("/transactions/<transaction_id>", methods=["PATCH"])
def update_transaction_endpoint(transaction_id):
    """update transaction status"""
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"error": "status is required"}), 400

    try:
        result = update_transaction(transaction_id, data["status"])
        return jsonify(result), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"error updating transaction: {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500


@transactions_bp.route("/transactions/<transaction_id>", methods=["DELETE"])
def delete_transaction_endpoint(transaction_id):
    """delete transaction"""
    try:
        result = delete_transaction(transaction_id)
        return jsonify(result), 200
    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"error deleting transaction: {e}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500
