"""pytest fixtures and configuration"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from app import app as flask_app
from db.connection import get_connection


@pytest.fixture
def app():
    flask_app.config.update({"TESTING": True})
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def cleanup_db():
    """cleanup test transactions after each test"""
    yield
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute("DELETE FROM transactions WHERE merchant_id LIKE 'TEST_%'")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    finally:
        cursor.close()
        conn.close()
