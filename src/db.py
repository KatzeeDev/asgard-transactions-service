"""
Database module with connection pooling and basic queries
"""

import mysql.connector
from mysql.connector import pooling
import os
import json
import logging

logger = logging.getLogger(__name__)

_connection_pool = None


def get_connection_pool():
    """
    get or create MySQL connection pool (singleton pattern) Reuses connections for better performance
    """
    global _connection_pool

    if _connection_pool is not None:
        return _connection_pool

    logger.info("Initializing database connection pool")

    _connection_pool = pooling.MySQLConnectionPool(
        pool_name="asgard_pool",
        pool_size=5,
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

    logger.info("Connection pool created successfully")
    return _connection_pool


def get_connection():
    # Get a connection from the pool
    pool = get_connection_pool()
    return pool.get_connection()


def get_transaction_by_order(merchant_id, order_reference):
    """
    idempotency check: transaction by merchant_id + order_reference
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

        # parse JSON metadata if exists
        if result and result.get("metadata"):
            result["metadata"] = json.loads(result["metadata"])

        return result
    finally:
        cursor.close()
        conn.close()


def get_transaction_by_id(transaction_id):
    """get transaction by transaction id"""
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
    """get all transactions from database"""
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

        # parse JSON metadata for each transaction
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
    """insert new transaction into database"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # metadata dict to JSON string
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
        logger.info(f"Transaction inserted: {transaction_id}")
        return transaction_id

    except mysql.connector.IntegrityError as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            raise ValueError(f"Transaction {transaction_id} already exists")
        elif "foreign key constraint" in str(e).lower():
            raise ValueError(
                f"Parent transaction {parent_transaction_id} does not exist"
            )
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting transaction: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
