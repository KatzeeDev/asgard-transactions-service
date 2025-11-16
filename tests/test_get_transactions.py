class TestGetTransactions:
    """test retrieval endpoints"""

    def test_get_all_transactions(self, client, cleanup_db):
        client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_GET_001",
                "order_reference": "ORDER_GET_001",
                "country_code": "CL",
            },
        )

        response = client.get("/transactions")
        assert response.status_code == 200
        data = response.get_json()
        assert "transactions" in data
        assert "total" in data
        assert isinstance(data["transactions"], list)

    def test_get_all_validates_fields(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 250.75,
                "currency": "USD",
                "merchant_id": "TEST_GET_FIELDS",
                "order_reference": "ORDER_GET_FIELDS",
                "country_code": "US",
                "metadata": {"test": "data"}
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.get("/transactions")
        data = response.get_json()

        txn = next((t for t in data["transactions"] if t["id"] == txn_id), None)
        assert txn is not None
        assert txn["type"] == "AUTH"
        assert txn["amount"] == "250.75"
        assert txn["currency"] == "USD"
        assert txn["merchant_id"] == "TEST_GET_FIELDS"
        assert txn["order_reference"] == "ORDER_GET_FIELDS"
        assert txn["country_code"] == "US"
        assert txn["status"] == "PENDING"
        assert "created_at" in txn
        assert "status_updated_at" in txn

    def test_get_single_with_all_fields(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1500.50,
                "currency": "EUR",
                "merchant_id": "TEST_GET_ALL_FIELDS",
                "order_reference": "ORDER_GET_ALL",
                "country_code": "ES",
                "metadata": {
                    "customer_id": "cust_123",
                    "email": "test@example.com"
                },
                "error_code": "TEST_CODE"
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.get(f"/transactions/{txn_id}")
        assert response.status_code == 200
        data = response.get_json()

        assert data["id"] == txn_id
        assert len(data["id"]) == 26
        assert data["type"] == "AUTH"
        assert data["amount"] == "1500.50"
        assert data["currency"] == "EUR"
        assert data["merchant_id"] == "TEST_GET_ALL_FIELDS"
        assert data["order_reference"] == "ORDER_GET_ALL"
        assert data["country_code"] == "ES"
        assert data["status"] == "PENDING"
        assert data.get("parent_id") is None
        assert data["metadata"]["customer_id"] == "cust_123"
        assert data["metadata"]["email"] == "test@example.com"
        assert data["error_code"] == "TEST_CODE"
        assert "created_at" in data
        assert "status_updated_at" in data

    def test_get_nonexistent_transaction(self, client):
        response = client.get("/transactions/NONEXISTENT_ID")
        assert response.status_code == 404
        assert "transaction not found" in response.get_json()["error"]
