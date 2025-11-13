"""
custom exceptions for business logic errors
"""

import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """base exception for application errors"""

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
    """business validation error"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class NotFoundError(AppError):
    """resource not found"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=404, payload=payload)


class DuplicateError(AppError):
    """resource already exists"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=409, payload=payload)


class DatabaseError(AppError):
    """database operation error"""

    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)


def register_error_handlers(app):

    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(f"app error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        logger.warning(f"validation error: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        logger.info(f"resource not found: {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"error": "endpoint not found"}), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({"error": "method not allowed"}), 405

    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f"internal server error: {error}", exc_info=True)
        return jsonify({"error": "internal server error"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        logger.warning(f"http exception: {error}")
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"unexpected error: {error}", exc_info=True)
        return jsonify({"error": "an unexpected error occurred"}), 500
