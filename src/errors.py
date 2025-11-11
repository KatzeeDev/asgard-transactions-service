"""
Error Handling Layer
"""

import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base exception for application errors"""

    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = {"error": self.message}
        if self.payload:
            rv.update(self.payload)
        return rv


class ValidationError(AppError):
    """Business validation error"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(AppError):
    """Resource not found"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)


class DuplicateError(AppError):
    """Resource already exists"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=409, payload=payload)


class DatabaseError(AppError):
    """Database operation error"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)


def register_error_handlers(app):
    """Register all error handlers with Flask app"""

    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(f"App error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        logger.warning(f"Validation error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        logger.info(f"Resource not found: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        logger.warning(f"HTTP exception: {error}")
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500
