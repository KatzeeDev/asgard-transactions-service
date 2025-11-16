import pytest


class TestUpdateTransaction:
    """test status updates"""

    @pytest.mark.parametrize("status", [
        "APPROVED",
        "DECLINED",
        "FAILED",
    ])
    def test_update_status(self, client, cleanup_db, status):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 500,
                "currency": "CLP",
                "merchant_id": f"TEST_UPDATE_{status}",
                "order_reference": f"ORDER_UPDATE_{status}",
                "country_code": "CL",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": status}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == status

    def test_update_invalid_status(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 200,
                "currency": "CLP",
                "merchant_id": "TEST_UPDATE_002",
                "order_reference": "ORDER_UPDATE_002",
                "country_code": "CL",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "INVALID_STATUS"}
        )
        assert response.status_code == 400
        assert "status must be one of" in response.get_json()["error"]

    def test_update_nonexistent_transaction(self, client):
        response = client.patch(
            "/transactions/NONEXISTENT", json={"status": "APPROVED"}
        )
        assert response.status_code == 404
