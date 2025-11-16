import pytest


class TestValidationErrors:
    """test input validation"""

    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            (
                {
                    "type": "AUTH",
                    "amount": 100,
                    "merchant_id": "M",
                    "order_reference": "O",
                    "country_code": "CL",
                },
                "currency is required",
            ),
            (
                {
                    "type": "AUTH",
                    "amount": -100,
                    "currency": "CLP",
                    "merchant_id": "M",
                    "order_reference": "O",
                    "country_code": "CL",
                },
                "amount must be greater than zero",
            ),
            (
                {
                    "type": "AUTH",
                    "amount": 100,
                    "currency": "XXX",
                    "merchant_id": "M",
                    "order_reference": "O",
                    "country_code": "CL",
                },
                "currency must be one of CLP, USD, EUR, GBP",
            ),
            (
                {
                    "type": "INVALID",
                    "amount": 100,
                    "currency": "CLP",
                    "merchant_id": "M",
                    "order_reference": "O",
                    "country_code": "CL",
                },
                "type must be one of AUTH, CAPTURE, REFUND",
            ),
        ],
    )
    def test_validation_errors(self, client, payload, expected_error):
        response = client.post("/transactions", json=payload)
        assert response.status_code == 400
        assert expected_error in response.get_json()["error"]
