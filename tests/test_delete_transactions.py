class TestDeleteTransaction:
    """test transaction deletion"""

    def test_delete_success(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 300,
                "currency": "USD",
                "merchant_id": "TEST_DELETE_001",
                "order_reference": "ORDER_DELETE_001",
                "country_code": "US",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.delete(f"/transactions/{txn_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["deleted"] is True

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

        get_response = client.get(f"/transactions/{txn_id}")
        assert get_response.status_code == 404

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

    def test_delete_capture_with_refund(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1000,
                "currency": "GBP",
                "merchant_id": "TEST_DELETE_CAP_REF",
                "order_reference": "ORDER_DELETE_CAP_REF_AUTH",
                "country_code": "GB",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 1000,
                "currency": "GBP",
                "merchant_id": "TEST_DELETE_CAP_REF",
                "order_reference": "ORDER_DELETE_CAP_REF_CAP",
                "country_code": "GB",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 500,
                "currency": "GBP",
                "merchant_id": "TEST_DELETE_CAP_REF",
                "order_reference": "ORDER_DELETE_CAP_REF_REF",
                "country_code": "GB",
                "parent_id": capture_id,
            },
        )

        response = client.delete(f"/transactions/{capture_id}")
        assert response.status_code == 400
        assert (
            "cannot delete transaction: it has child transactions"
            in response.get_json()["error"]
        )

    def test_delete_refund_success(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 2000,
                "currency": "USD",
                "merchant_id": "TEST_DELETE_REF_OK",
                "order_reference": "ORDER_DELETE_REF_OK_AUTH",
                "country_code": "US",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 2000,
                "currency": "USD",
                "merchant_id": "TEST_DELETE_REF_OK",
                "order_reference": "ORDER_DELETE_REF_OK_CAP",
                "country_code": "US",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        refund_response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 500,
                "currency": "USD",
                "merchant_id": "TEST_DELETE_REF_OK",
                "order_reference": "ORDER_DELETE_REF_OK_REF",
                "country_code": "US",
                "parent_id": capture_id,
            },
        )
        refund_id = refund_response.get_json()["id"]

        delete_response = client.delete(f"/transactions/{refund_id}")
        assert delete_response.status_code == 200
        assert delete_response.get_json()["deleted"] is True

        get_response = client.get(f"/transactions/{refund_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_transaction(self, client):
        response = client.delete("/transactions/NONEXISTENT")
        assert response.status_code == 404

    def test_delete_cascade_order(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 3000,
                "currency": "EUR",
                "merchant_id": "TEST_DELETE_CASCADE",
                "order_reference": "ORDER_DELETE_CASCADE_AUTH",
                "country_code": "ES",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 3000,
                "currency": "EUR",
                "merchant_id": "TEST_DELETE_CASCADE",
                "order_reference": "ORDER_DELETE_CASCADE_CAP",
                "country_code": "ES",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        refund_response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 1000,
                "currency": "EUR",
                "merchant_id": "TEST_DELETE_CASCADE",
                "order_reference": "ORDER_DELETE_CASCADE_REF",
                "country_code": "ES",
                "parent_id": capture_id,
            },
        )
        refund_id = refund_response.get_json()["id"]

        delete_refund = client.delete(f"/transactions/{refund_id}")
        assert delete_refund.status_code == 200

        delete_capture = client.delete(f"/transactions/{capture_id}")
        assert delete_capture.status_code == 200

        delete_auth = client.delete(f"/transactions/{auth_id}")
        assert delete_auth.status_code == 200

    def test_delete_transaction_with_metadata(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 750,
                "currency": "CLP",
                "merchant_id": "TEST_DELETE_META",
                "order_reference": "ORDER_DELETE_META",
                "country_code": "CL",
                "metadata": {"customer_id": "cust_456", "notes": "Test transaction"},
            },
        )
        txn_id = create_response.get_json()["id"]

        delete_response = client.delete(f"/transactions/{txn_id}")
        assert delete_response.status_code == 200

        get_response = client.get(f"/transactions/{txn_id}")
        assert get_response.status_code == 404

    def test_delete_transaction_with_final_status(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1200,
                "currency": "USD",
                "merchant_id": "TEST_DELETE_FINAL",
                "order_reference": "ORDER_DELETE_FINAL",
                "country_code": "US",
            },
        )
        txn_id = create_response.get_json()["id"]

        client.patch(f"/transactions/{txn_id}", json={"status": "APPROVED"})

        delete_response = client.delete(f"/transactions/{txn_id}")
        assert delete_response.status_code == 200

        get_response = client.get(f"/transactions/{txn_id}")
        assert get_response.status_code == 404
