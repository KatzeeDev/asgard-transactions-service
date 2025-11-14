"""
database queries for transactions
"""

import json
import logging
import mysql.connector
from db.connection import get_connection

logger = logging.getLogger(__name__)


def get_transaction_by_idempotency_key(idempotency_key):
    """find transaction by idempotency key"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, idempotency_key, type, amount, currency,
                   merchant_id, order_reference, parent_id, metadata, status,
                   error_code, country_code, created_at, status_updated_at, processed_at
            FROM transactions
            WHERE idempotency_key = %s
        """,
            (idempotency_key,),
        )

        result = cursor.fetchone()

        if result and result.get("metadata"):
            result["metadata"] = json.loads(result["metadata"])

        return result
    finally:
        cursor.close()
        conn.close()


def get_transaction_by_id(transaction_id):
    """find transaction by id"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, idempotency_key, type, amount, currency,
                   merchant_id, order_reference, parent_id, metadata, status,
                   error_code, country_code, created_at, status_updated_at, processed_at
            FROM transactions
            WHERE id = %s
        """,
            (transaction_id,),
        )

        result = cursor.fetchone()

        if result and result.get("metadata"):
            result["metadata"] = json.loads(result["metadata"])

        return result
    finally:
        cursor.close()
        conn.close()


def get_all_transactions():
    """fetch all transactions ordered by newest"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, idempotency_key, type, amount, currency,
                   merchant_id, order_reference, parent_id, metadata, status,
                   error_code, country_code, created_at, status_updated_at, processed_at
            FROM transactions
            ORDER BY created_at DESC
        """
        )

        results = cursor.fetchall()

        for result in results:
            if result.get("metadata"):
                result["metadata"] = json.loads(result["metadata"])

        return results
    finally:
        cursor.close()
        conn.close()


def insert_transaction(
    transaction_id,
    idempotency_key,
    transaction_type,
    amount,
    currency,
    merchant_id,
    order_reference,
    country_code,
    parent_id=None,
    metadata=None,
    status="PENDING",
    error_code=None,
):
    """create new transaction in database"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # convert metadata dict to json string
        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute(
            """
            INSERT INTO transactions (
                id, idempotency_key, type, amount, currency, merchant_id,
                order_reference, parent_id, metadata, status,
                error_code, country_code
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                transaction_id,
                idempotency_key,
                transaction_type,
                amount,
                currency,
                merchant_id,
                order_reference,
                parent_id,
                metadata_json,
                status,
                error_code,
                country_code,
            ),
        )

        conn.commit()
        logger.info(f"transaction inserted: {transaction_id}")
        return transaction_id

    except mysql.connector.IntegrityError as e:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"error inserting transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def update_transaction_status(transaction_id, new_status):
    """change transaction status and update status_updated_at"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # update status and status_updated_at timestamp
        cursor.execute(
            """
            UPDATE transactions
            SET status = %s, status_updated_at = CURRENT_TIMESTAMP(3)
            WHERE id = %s
            """,
            (new_status, transaction_id),
        )
        conn.commit()
        rows_affected = cursor.rowcount
        if rows_affected == 0:
            return False
        logger.info(f"transaction status updated: {transaction_id} -> {new_status}")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"error updating transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def set_processed_timestamp(transaction_id):
    """set processed_at timestamp when transaction completes"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE transactions
            SET processed_at = CURRENT_TIMESTAMP(3)
            WHERE id = %s AND processed_at IS NULL
            """,
            (transaction_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"error setting processed_at: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def delete_transaction(transaction_id):
    """remove transaction from database"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM transactions WHERE id = %s",
            (transaction_id,),
        )
        conn.commit()
        rows_affected = cursor.rowcount
        if rows_affected == 0:
            return False
        logger.info(f"transaction deleted: {transaction_id}")
        return True
    except mysql.connector.IntegrityError as e:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"error deleting transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
