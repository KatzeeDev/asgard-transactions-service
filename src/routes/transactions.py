"""
http endpoints for transaction operations handles request/response and delegates to service layer
"""

import json
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
from utils import remove_nulls

logger = logging.getLogger(__name__)

# blueprint for transaction routes
transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/transactions", methods=["GET"])
def list_transactions_endpoint():
    """get all transactions"""
    result = list_transactions()
    return jsonify(remove_nulls(result)), 200


@transactions_bp.route("/transactions", methods=["POST"])
def create_transaction_endpoint():
    """create new transaction"""
    try:
        data = json.loads(request.get_data(as_text=True))
    except (json.JSONDecodeError, ValueError):
        raise ValidationError("invalid json")

    if not data:
        raise ValidationError("invalid json")

    result = create_transaction(
        transaction_type=data.get("type"),
        amount=data.get("amount"),
        currency=data.get("currency"),
        merchant_id=data.get("merchant_id"),
        order_reference=data.get("order_reference"),
        country_code=data.get("country_code"),
        parent_id=data.get("parent_id"),
        metadata=data.get("metadata"),
        error_code=data.get("error_code"),
    )

    if result["is_duplicate"]:
        return (
            jsonify(
                {
                    "message": "transaction already exists",
                    "id": result["id"],
                    "status": result["status"],
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "message": "transaction created successfully",
                "id": result["id"],
                "status": result["status"],
            }
        ),
        201,
    )


@transactions_bp.route("/transactions/<transaction_id>", methods=["GET"])
def get_transaction_endpoint(transaction_id):
    """get single transaction by id"""
    transaction = get_transaction(transaction_id)
    if not transaction:
        raise NotFoundError("transaction not found")
    return jsonify(remove_nulls(transaction)), 200


@transactions_bp.route("/transactions/<transaction_id>", methods=["PATCH"])
def update_transaction_endpoint(transaction_id):
    """update transaction status"""
    try:
        data = json.loads(request.get_data(as_text=True))
    except (json.JSONDecodeError, ValueError):
        raise ValidationError("invalid json")

    if not data or "status" not in data:
        raise ValidationError("status is required")

    result = update_transaction(transaction_id, data["status"])
    return jsonify(remove_nulls(result)), 200


@transactions_bp.route("/transactions/<transaction_id>", methods=["DELETE"])
def delete_transaction_endpoint(transaction_id):
    """delete transaction"""
    result = delete_transaction(transaction_id)
    return jsonify(remove_nulls(result)), 200
