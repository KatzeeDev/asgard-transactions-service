"""
bussines logic layer... this maybe changue but its a start.
"""

import logging
from typing import Optional, Dict, Any
from db import (
    get_transaction_by_order,
    get_transaction_by_id,
    insert_transaction,
    get_all_transactions,
)
from utils import generate_transaction_id
from errors import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

ALLOWED_CURRENCIES = ("CLP", "USD", "EUR")
ALLOWED_TRANSACTION_TYPES = ("AUTH", "CAPTURE", "REFUND")


def create_transaction(
    transaction_type: str,
    amount: Any,
    currency: str,
    merchant_id: str,
    order_reference: str,
    parent_transaction_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    login validation for a new transaction
    """
    logger.info(
        f"Creating transaction: type={transaction_type}, merchant={merchant_id}, order={order_reference}"
    )

    # idempotency check
    existing = get_transaction_by_order(merchant_id, order_reference)
    if existing:
        logger.info(
            f"Transaction already exists (idempotent): {existing['transaction_id']}"
        )
        return {
            "transaction_id": existing["transaction_id"],
            "status": existing["status"],
            "is_duplicate": True,
        }

    # validate amount
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero")
    except (TypeError, ValueError):
        raise ValidationError("Invalid amount")

    # validate currency
    if currency not in ALLOWED_CURRENCIES:
        raise ValidationError(
            f"Currency must be one of {', '.join(ALLOWED_CURRENCIES)}"
        )

    # validate transaction type
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValidationError(
            f"Type must be one of {', '.join(ALLOWED_TRANSACTION_TYPES)}"
        )

    # business rule: CAPTURE and REFUND need parent_transaction_id
    if transaction_type in ("CAPTURE", "REFUND"):
        if not parent_transaction_id:
            raise ValidationError(f"{transaction_type} requires parent_transaction_id")

        parent = get_transaction_by_id(parent_transaction_id)
        if not parent:
            raise ValidationError("Parent transaction not found")

        # business rule: CAPTURE must reference AUTH
        if transaction_type == "CAPTURE" and parent["type"] != "AUTH":
            raise ValidationError("CAPTURE must reference an AUTH")

        # business rule: REFUND must reference AUTH or CAPTURE
        if transaction_type == "REFUND" and parent["type"] not in ("AUTH", "CAPTURE"):
            raise ValidationError("REFUND must reference AUTH or CAPTURE")

    # business rule: AUTH cannot have parent
    if transaction_type == "AUTH" and parent_transaction_id:
        raise ValidationError("AUTH cannot have parent_transaction_id")

    # validate metadata
    if metadata and not isinstance(metadata, dict):
        raise ValidationError("metadata must be a JSON object")

    # generate unique transaction ID
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

    logger.info(f"Transaction created successfully: {transaction_id}")

    return {
        "transaction_id": transaction_id,
        "status": "PENDING",
        "is_duplicate": False,
    }


def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    """
    get transaction by id
    """
    logger.info(f"Retrieving transaction: {transaction_id}")
    transaction = get_transaction_by_id(transaction_id)

    if not transaction:
        logger.warning(f"Transaction not found: {transaction_id}")
        return None

    return transaction


def list_transactions() -> Dict[str, Any]:
    """
    get all transactions
    """
    logger.info("Retrieving all transactions")
    transactions = get_all_transactions()

    return {"transactions": transactions, "total": len(transactions)}
