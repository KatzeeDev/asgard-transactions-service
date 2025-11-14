"""
business logic for transactions
handles validation and orchestrates db operations
"""

import logging
import mysql.connector
from typing import Optional, Dict, Any
from db.queries import (
    get_transaction_by_idempotency_key,
    get_transaction_by_id,
    insert_transaction,
    get_all_transactions,
    update_transaction_status,
    set_processed_timestamp,
    delete_transaction as db_delete_transaction,
)
from utils import generate_transaction_id, generate_idempotency_key
from exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

# business constants
ALLOWED_CURRENCIES = ("CLP", "USD", "EUR", "GBP")
ALLOWED_TRANSACTION_TYPES = ("AUTH", "CAPTURE", "REFUND")
ALLOWED_STATUSES = (
    "PENDING",
    "PROCESSING",
    "APPROVED",
    "DECLINED",
    "EXPIRED",
    "CANCELLED",
    "FAILED",
)
ALLOWED_COUNTRIES = ("CL", "US", "ES", "GB", "SE", "BR", "AR", "MX", "CO", "PE", "UY")

# final states that trigger processed_at timestamp
FINAL_STATUSES = ("APPROVED", "DECLINED", "FAILED", "EXPIRED", "CANCELLED")


def create_transaction(
    transaction_type: Optional[str] = None,
    amount: Optional[Any] = None,
    currency: Optional[str] = None,
    merchant_id: Optional[str] = None,
    order_reference: Optional[str] = None,
    country_code: Optional[str] = None,
    parent_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    create a new transaction with full business validation
    """
    logger.info(
        f"creating transaction: type={transaction_type}, merchant={merchant_id}, order={order_reference}"
    )

    required_fields = {
        "type": transaction_type,
        "amount": amount,
        "currency": currency,
        "merchant_id": merchant_id,
        "order_reference": order_reference,
        "country_code": country_code,
    }

    for field_name, field_value in required_fields.items():
        if field_value is None:
            raise ValidationError(f"{field_name} is required")

    # validate amount is positive number
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValidationError("amount must be greater than zero")
    except (TypeError, ValueError):
        raise ValidationError("invalid amount")

    # validate currency against allowed list
    if currency not in ALLOWED_CURRENCIES:
        raise ValidationError(
            f"currency must be one of {', '.join(ALLOWED_CURRENCIES)}"
        )

    # validate transaction type
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValidationError(
            f"type must be one of {', '.join(ALLOWED_TRANSACTION_TYPES)}"
        )

    # validate country_code -> ISO 3166-1
    if not country_code:
        raise ValidationError("country_code is required")
    if country_code not in ALLOWED_COUNTRIES:
        raise ValidationError(
            f"country_code must be one of {', '.join(ALLOWED_COUNTRIES)}"
        )

    # business rule: capture and refund need parent transaction
    if transaction_type in ("CAPTURE", "REFUND"):
        if not parent_id:
            raise ValidationError(f"{transaction_type} requires parent_id")

        parent = get_transaction_by_id(parent_id)
        if not parent:
            raise ValidationError("parent transaction not found")

        # business rule: capture must reference auth
        if transaction_type == "CAPTURE" and parent["type"] != "AUTH":
            raise ValidationError("capture must reference an auth transaction")

        # business rule: refund must reference auth or capture
        if transaction_type == "REFUND" and parent["type"] not in ("AUTH", "CAPTURE"):
            raise ValidationError("refund must reference auth or capture")

    # business rule: auth cannot have parent
    if transaction_type == "AUTH" and parent_id:
        raise ValidationError("auth cannot have parent_id")

    # validate metadata is dict
    if metadata and not isinstance(metadata, dict):
        raise ValidationError("metadata must be a json object")

    # generate unique transaction id and idempotency key
    transaction_id = generate_transaction_id()
    idempotency_key = generate_idempotency_key(
        merchant_id, order_reference, amount, currency, transaction_type, country_code
    )

    try:
        insert_transaction(
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            merchant_id=merchant_id,
            order_reference=order_reference,
            country_code=country_code,
            parent_id=parent_id,
            metadata=metadata,
            status="PENDING",
            error_code=error_code,
        )
    except mysql.connector.IntegrityError as e:
        error_msg = str(e)
        if "Duplicate entry" in error_msg:
            if "idempotency_key" in error_msg:
                logger.info(f"duplicate request detected within 5min window")
                existing = get_transaction_by_idempotency_key(idempotency_key)
                return {
                    "id": existing["id"],
                    "status": existing["status"],
                    "is_duplicate": True,
                }
            raise ValidationError(f"transaction {transaction_id} already exists")
        elif "foreign key constraint" in error_msg.lower():
            raise ValidationError(f"parent transaction {parent_id} does not exist")
        raise

    logger.info(f"transaction created successfully: {transaction_id}")

    return {
        "id": transaction_id,
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

    # set processed_at timestamp if moving to final state
    if status in FINAL_STATUSES:
        set_processed_timestamp(transaction_id)

    logger.info(f"transaction {transaction_id} updated successfully")
    return {"id": transaction_id, "status": status}


def delete_transaction(transaction_id: str) -> Dict[str, Any]:
    """delete transaction if it has no dependencies"""
    logger.info(f"deleting transaction {transaction_id}")

    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        raise NotFoundError(f"transaction {transaction_id} not found")

    try:
        success = db_delete_transaction(transaction_id)
        if not success:
            raise NotFoundError(f"transaction {transaction_id} not found")
        logger.info(f"transaction {transaction_id} deleted successfully")
        return {"id": transaction_id, "deleted": True}
    except mysql.connector.IntegrityError as e:
        if "foreign key constraint" in str(e).lower():
            raise ValidationError(
                "cannot delete transaction: it has child transactions"
            )
        raise
