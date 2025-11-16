class TestDeleteTransaction:
    """test transaction deletion"""

    def test_delete_auth_no_children(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 500,
                "currency": "EUR",
                "merchant_id": "TEST_DELETE_AUTH",
                "order_reference": "ORDER_DELETE_AUTH",
                "country_code": "ES",
            },
        )
        txn_id = create_response.get_json()["id"]

        delete_response = client.delete(f"/transactions/{txn_id}")
        assert delete_response.status_code == 200
        assert delete_response.get_json()["deleted"] is True

    def test_delete_with_children(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 400,
                "currency": "CLP",
                "merchant_id": "TEST_DELETE_002",
                "order_reference": "ORDER_DELETE_002",
                "country_code": "CL",
            },
        )
        auth_id = auth_response.get_json()["id"]

        client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 400,
                "currency": "CLP",
                "merchant_id": "TEST_DELETE_002",
                "order_reference": "ORDER_DELETE_003",
                "country_code": "CL",
                "parent_id": auth_id,
            },
        )

        response = client.delete(f"/transactions/{auth_id}")
        assert response.status_code == 400
        assert (
            "cannot delete transaction: it has child transactions"
            in response.get_json()["error"]
        )

    def test_delete_nonexistent_transaction(self, client):
        response = client.delete("/transactions/NONEXISTENT")
        assert response.status_code == 404
