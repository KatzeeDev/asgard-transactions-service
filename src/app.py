"""
Asgard Transactions API
"""

import os
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify
from utils import CustomJSONProvider
from exceptions import register_error_handlers
from werkzeug.exceptions import (
    BadRequest,
    MethodNotAllowed,
    NotFound,
    InternalServerError,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.json = CustomJSONProvider(app)

from routes.transactions import transactions_bp

app.register_blueprint(transactions_bp)

register_error_handlers(app)


@app.errorhandler(BadRequest)
def handle_bad_request_override(error):
    logger.warning(f"bad request intercepted: {error.description}")
    return jsonify({"error": "invalid json"}), 400


@app.errorhandler(MethodNotAllowed)
def handle_method_not_allowed_override(error):
    logger.warning(f"method not allowed: {error.description}")
    return jsonify({"error": "method not allowed"}), 405


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"starting asgard api on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
