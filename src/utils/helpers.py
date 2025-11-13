"""
helper functions for the application
"""

import secrets
from datetime import datetime


def generate_transaction_id(transaction_type):
    """
    generate unique transaction id
    format: TXN_YYYYMMDD_HHMMSS_TYPE_RANDOM
    example: TXN_20250110_143052_AUTH_a3f9k2p8
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(4)  # 8 hex chars for uniqueness
    return f"TXN_{timestamp}_{transaction_type}_{random_suffix}"
