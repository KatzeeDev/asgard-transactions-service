from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Union
from flask.json.provider import DefaultJSONProvider

ISO8601_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
MILLISECOND_PRECISION = -3


class CustomJSONProvider(DefaultJSONProvider):
    """custom JSON serializer for flask responses"""

    def default(self, obj: Any) -> Any:
        """serialize custom types to json-compatible formats"""
        serializers = {
            datetime: self._serialize_datetime,
            Decimal: self._serialize_decimal,
        }

        serializer = serializers.get(type(obj))
        if serializer:
            return serializer(obj)

        return super().default(obj)

    @staticmethod
    def _serialize_datetime(dt: datetime) -> str:
        """convert datetime to ISO 8601 string with millisecond"""
        return dt.strftime(ISO8601_FORMAT)[:MILLISECOND_PRECISION] + "Z"

    @staticmethod
    def _serialize_decimal(dec: Decimal) -> str:
        """convert Decimal to string preserving precision"""
        return str(dec)


def remove_nulls(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    recursively remove None values from dictionaries and lists
    preserves structure while filtering out null/None values
    useful for cleaning API responses
    """
    if isinstance(data, dict):
        return {
            key: remove_nulls(value) for key, value in data.items() if value is not None
        }

    if isinstance(data, list):
        return [remove_nulls(item) for item in data]

    return data
