"""
singleton pattern for mysql connection pool
"""

import os
import logging
from mysql.connector import pooling

logger = logging.getLogger(__name__)

_connection_pool = None


def get_connection_pool():
    """create the singleton connection pool"""
    global _connection_pool

    if _connection_pool is not None:
        return _connection_pool

    logger.info("initializing database connection pool")

    _connection_pool = pooling.MySQLConnectionPool(
        pool_name="asgard_pool",
        pool_size=5,
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

    logger.info("connection pool created successfully")
    return _connection_pool


def get_connection():
    """get a connection from the pool"""
    pool = get_connection_pool()
    return pool.get_connection()
