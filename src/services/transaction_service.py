"""
business logic for transactions
handles validation and orchestrates db operations
"""

import logging
from typing import Optional, Dict, Any
from db.queries import (
    get_transaction_by_order,
    get_transaction_by_id,
    insert_transaction,
    get_all_transactions,
    update_transaction_status,
    delete_transaction as db_delete_transaction,
)
from utils import generate_transaction_id
from exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

# business constants
ALLOWED_CURRENCIES = ("CLP", "USD", "EUR")
ALLOWED_TRANSACTION_TYPES = ("AUTH", "CAPTURE", "REFUND")
ALLOWED_STATUSES = ("PENDING", "APPROVED", "DECLINED")


def create_transaction(
    transaction_type: str,
    amount: Any,
    currency: str,
    merchant_id: str,
    order_reference: str,
    parent_transaction_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    create a new transaction with full business validation
    """
    logger.info(
        f"creating transaction: type={transaction_type}, merchant={merchant_id}, order={order_reference}"
    )

    # idempotency check - prevent duplicate transactions
    existing = get_transaction_by_order(merchant_id, order_reference)
    if existing:
        logger.info(f"transaction already exists (idempotent): {existing['transaction_id']}")
        return {
            "transaction_id": existing["transaction_id"],
            "status": existing["status"],
            "is_duplicate": True,
        }

    # validate amount is positive number
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValidationError("amount must be greater than zero")
    except (TypeError, ValueError):
        raise ValidationError("invalid amount")

    # validate currency against allowed list
    if currency not in ALLOWED_CURRENCIES:
        raise ValidationError(f"currency must be one of {', '.join(ALLOWED_CURRENCIES)}")

    # validate transaction type
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValidationError(f"type must be one of {', '.join(ALLOWED_TRANSACTION_TYPES)}")

    # business rule: capture and refund need parent transaction
    if transaction_type in ("CAPTURE", "REFUND"):
        if not parent_transaction_id:
            raise ValidationError(f"{transaction_type} requires parent_transaction_id")

        parent = get_transaction_by_id(parent_transaction_id)
        if not parent:
            raise ValidationError("parent transaction not found")

        # business rule: capture must reference auth
        if transaction_type == "CAPTURE" and parent["type"] != "AUTH":
            raise ValidationError("capture must reference an auth transaction")

        # business rule: refund must reference auth or capture
        if transaction_type == "REFUND" and parent["type"] not in ("AUTH", "CAPTURE"):
            raise ValidationError("refund must reference auth or capture")

    # business rule: auth cannot have parent
    if transaction_type == "AUTH" and parent_transaction_id:
        raise ValidationError("auth cannot have parent_transaction_id")

    # validate metadata is dict
    if metadata and not isinstance(metadata, dict):
        raise ValidationError("metadata must be a json object")

    # generate unique transaction id
    transaction_id = generate_transaction_id(transaction_type)

    # save to database
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
        error_code=error_code,
        error_message=error_message,
        location=location,
    )

    logger.info(f"transaction created successfully: {transaction_id}")

    return {
        "transaction_id": transaction_id,
        "status": "PENDING",
        "is_duplicate": False,
    }


def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    """retrieve single transaction by id"""
    logger.info(f"retrieving transaction: {transaction_id}")
    transaction = get_transaction_by_id(transaction_id)

    if not transaction:
        logger.warning(f"transaction not found: {transaction_id}")
        return None

    return transaction


def list_transactions() -> Dict[str, Any]:
    """get all transactions from the system"""
    logger.info("retrieving all transactions")
    transactions = get_all_transactions()

    return {"transactions": transactions, "total": len(transactions)}


def update_transaction(transaction_id: str, status: str) -> Dict[str, Any]:
    """update transaction status with validation"""
    logger.info(f"updating transaction {transaction_id} to status {status}")

    # verify transaction exists
    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        raise NotFoundError(f"transaction {transaction_id} not found")

    # validate status against allowed values
    if status not in ALLOWED_STATUSES:
        raise ValidationError(f"status must be one of {', '.join(ALLOWED_STATUSES)}")

    # update in database
    success = update_transaction_status(transaction_id, status)
    if not success:
        raise NotFoundError(f"transaction {transaction_id} not found")

    logger.info(f"transaction {transaction_id} updated successfully")
    return {"transaction_id": transaction_id, "status": status}


def delete_transaction(transaction_id: str) -> Dict[str, Any]:
    """delete transaction if it has no dependencies"""
    logger.info(f"deleting transaction {transaction_id}")

    # verify transaction exists
    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        raise NotFoundError(f"transaction {transaction_id} not found")

    # attempt deletion
    try:
        success = db_delete_transaction(transaction_id)
        if not success:
            raise NotFoundError(f"transaction {transaction_id} not found")
        logger.info(f"transaction {transaction_id} deleted successfully")
        return {"transaction_id": transaction_id, "deleted": True}
    except ValueError as e:
        raise ValidationError(str(e))
