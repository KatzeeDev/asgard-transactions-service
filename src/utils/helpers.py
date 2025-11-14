"""
helper functions for the application
"""

import hashlib
import time
from ulid import ULID


def generate_transaction_id():
    """generate unique transaction id using ULID"""
    return str(ULID())


def generate_idempotency_key(
    merchant_id, order_reference, amount, currency, transaction_type, country_code
):
    """
    generate idempotency fingerprint
    works with 5-minute temporal window detects duplicate requests within window.
    allows retries after
    """
    current_time = int(time.time())
    window = int(current_time / 300) * 300

    fingerprint = f"{merchant_id}|{order_reference}|{amount}|{currency}|{transaction_type}|{country_code}|{window}"
    return hashlib.sha256(fingerprint.encode()).hexdigest()
