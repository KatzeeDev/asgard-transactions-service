"""
Asgard Transactions API
"""

import os
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify

# Load environment variables
load_dotenv()

# logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# register blueprints
from routes.transactions import transactions_bp

app.register_blueprint(transactions_bp)


# global error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"internal error: {error}")
    return jsonify({"error": "internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"starting asgard api on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
