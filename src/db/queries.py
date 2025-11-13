"""
database queries for transactions
"""

import json
import logging
import mysql.connector
from db.connection import get_connection

logger = logging.getLogger(__name__)


def get_transaction_by_order(merchant_id, order_reference):
    """
    check if transaction exists by merchant and order -> used for idempotency
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT transaction_id, type, amount, currency, merchant_id,
                   order_reference, parent_transaction_id, metadata, status,
                   created_at, updated_at
            FROM transactions
            WHERE merchant_id = %s AND order_reference = %s
        """,
            (merchant_id, order_reference),
        )

        result = cursor.fetchone()

        # parse json metadata
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
            SELECT transaction_id, type, amount, currency, merchant_id,
                   order_reference, parent_transaction_id, metadata, status,
                   created_at, updated_at
            FROM transactions
            WHERE transaction_id = %s
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
            SELECT transaction_id, type, amount, currency, merchant_id,
                   order_reference, parent_transaction_id, metadata, status,
                   created_at, updated_at
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
    transaction_type,
    amount,
    currency,
    merchant_id,
    order_reference,
    parent_transaction_id=None,
    metadata=None,
    status="PENDING",
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
                transaction_id, type, amount, currency, merchant_id,
                order_reference, parent_transaction_id, metadata, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                transaction_id,
                transaction_type,
                amount,
                currency,
                merchant_id,
                order_reference,
                parent_transaction_id,
                metadata_json,
                status,
            ),
        )

        conn.commit()
        logger.info(f"transaction inserted: {transaction_id}")
        return transaction_id

    except mysql.connector.IntegrityError as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            raise ValueError(f"transaction {transaction_id} already exists")
        elif "foreign key constraint" in str(e).lower():
            raise ValueError(
                f"parent transaction {parent_transaction_id} does not exist"
            )
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"error inserting transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def update_transaction_status(transaction_id, new_status):
    """change transaction status"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE transactions SET status = %s WHERE transaction_id = %s",
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


def delete_transaction(transaction_id):
    """remove transaction from database"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM transactions WHERE transaction_id = %s",
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
        if "foreign key constraint" in str(e).lower():
            raise ValueError("cannot delete transaction: it has child transactions")
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"error deleting transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
