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

    def test_get_single_transaction(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 500,
                "currency": "USD",
                "merchant_id": "TEST_GET_002",
                "order_reference": "ORDER_GET_002",
                "country_code": "US",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.get(f"/transactions/{txn_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == txn_id
        assert data["amount"] == "500.00"
        assert data["country_code"] == "US"

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

    def test_get_capture_with_parent(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 2000,
                "currency": "GBP",
                "merchant_id": "TEST_GET_PARENT",
                "order_reference": "ORDER_GET_PARENT_AUTH",
                "country_code": "GB",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 2000,
                "currency": "GBP",
                "merchant_id": "TEST_GET_PARENT",
                "order_reference": "ORDER_GET_PARENT_CAP",
                "country_code": "GB",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        response = client.get(f"/transactions/{capture_id}")
        data = response.get_json()

        assert data["type"] == "CAPTURE"
        assert data["parent_id"] == auth_id
        assert "created_at" in data

    def test_get_with_metadata(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 750,
                "currency": "CLP",
                "merchant_id": "TEST_GET_META",
                "order_reference": "ORDER_GET_META",
                "country_code": "CL",
                "metadata": {
                    "session_id": "sess_abc123",
                    "user_agent": "Mozilla/5.0",
                    "items": [
                        {"id": 1, "name": "Product A"},
                        {"id": 2, "name": "Product B"}
                    ]
                }
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.get(f"/transactions/{txn_id}")
        data = response.get_json()

        assert data["metadata"]["session_id"] == "sess_abc123"
        assert data["metadata"]["user_agent"] == "Mozilla/5.0"
        assert len(data["metadata"]["items"]) == 2
        assert data["metadata"]["items"][0]["name"] == "Product A"

    def test_get_transaction_with_final_status(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1000,
                "currency": "USD",
                "merchant_id": "TEST_GET_FINAL",
                "order_reference": "ORDER_GET_FINAL",
                "country_code": "US",
            },
        )
        txn_id = create_response.get_json()["id"]

        client.patch(f"/transactions/{txn_id}", json={"status": "APPROVED"})

        response = client.get(f"/transactions/{txn_id}")
        data = response.get_json()

        assert data["status"] == "APPROVED"
        assert data["processed_at"] is not None
        assert "created_at" in data
        assert "status_updated_at" in data

    def test_get_multiple_transactions_ordered(self, client, cleanup_db):
        for i in range(5):
            client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": 100 + i,
                    "currency": "CLP",
                    "merchant_id": f"TEST_GET_ORDER_{i}",
                    "order_reference": f"ORDER_{i}",
                    "country_code": "CL",
                },
            )

        response = client.get("/transactions")
        data = response.get_json()

        assert data["total"] >= 5
        assert len(data["transactions"]) >= 5

    def test_get_transactions_all_types(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 3000,
                "currency": "EUR",
                "merchant_id": "TEST_GET_TYPES",
                "order_reference": "ORDER_TYPES_AUTH",
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
                "merchant_id": "TEST_GET_TYPES",
                "order_reference": "ORDER_TYPES_CAP",
                "country_code": "ES",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        refund_response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 500,
                "currency": "EUR",
                "merchant_id": "TEST_GET_TYPES",
                "order_reference": "ORDER_TYPES_REF",
                "country_code": "ES",
                "parent_id": capture_id,
            },
        )
        refund_id = refund_response.get_json()["id"]

        auth_data = client.get(f"/transactions/{auth_id}").get_json()
        capture_data = client.get(f"/transactions/{capture_id}").get_json()
        refund_data = client.get(f"/transactions/{refund_id}").get_json()

        assert auth_data["type"] == "AUTH"
        assert capture_data["type"] == "CAPTURE"
        assert refund_data["type"] == "REFUND"

    def test_get_with_different_currencies(self, client, cleanup_db):
        currencies = ["CLP", "USD", "EUR", "GBP"]
        txn_ids = []

        for currency in currencies:
            response = client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": 500,
                    "currency": currency,
                    "merchant_id": f"TEST_GET_CURR_{currency}",
                    "order_reference": f"ORDER_CURR_{currency}",
                    "country_code": "CL",
                },
            )
            txn_ids.append(response.get_json()["id"])

        for i, currency in enumerate(currencies):
            response = client.get(f"/transactions/{txn_ids[i]}")
            data = response.get_json()
            assert data["currency"] == currency

    def test_get_with_error_codes(self, client, cleanup_db):
        error_codes = ["INSUFFICIENT_FUNDS", "CARD_EXPIRED", "FRAUD_SUSPECTED"]
        txn_ids = []

        for error_code in error_codes:
            response = client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": 200,
                    "currency": "USD",
                    "merchant_id": f"TEST_GET_ERR_{error_code}",
                    "order_reference": f"ORDER_ERR_{error_code}",
                    "country_code": "US",
                    "error_code": error_code
                },
            )
            txn_ids.append(response.get_json()["id"])

        for i, error_code in enumerate(error_codes):
            response = client.get(f"/transactions/{txn_ids[i]}")
            data = response.get_json()
            assert data["error_code"] == error_code
