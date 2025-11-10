import secrets
from datetime import datetime


def generate_transaction_id(transaction_type):
    """
    Generate unique transaction ID
    Format: TXN_YYYYMMDD_HHMMSS_TYPE_RANDOM
    Example: TXN_20250110_143052_AUTH_a3f9k2p8
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(4)  # 8 hex chars for uniqueness, to start.
    return f"TXN_{timestamp}_{transaction_type}_{random_suffix}"
