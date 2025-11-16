import pytest


class TestCreateTransactions:
    """test transaction creation"""

    def test_create_auth_success(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 10000.50,
                "currency": "CLP",
                "merchant_id": "TEST_MERCHANT_001",
                "order_reference": "ORDER_001",
                "country_code": "CL",
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert "status" in data
        assert "message" in data
        assert len(data["id"]) == 26
        assert data["status"] == "PENDING"
        assert data["message"] == "transaction created successfully"

    def test_create_auth_with_metadata(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 5000,
                "currency": "USD",
                "merchant_id": "TEST_MERCHANT_META",
                "order_reference": "ORDER_META_001",
                "country_code": "US",
                "metadata": {
                    "customer_email": "test@example.com",
                    "customer_name": "John Doe",
                    "device": "mobile",
                    "ip_address": "192.168.1.1",
                    "cart_items": ["item1", "item2"],
                },
            },
        )
        assert response.status_code == 201

    @pytest.mark.parametrize("currency", ["CLP", "USD"])
    def test_create_auth_currency(self, client, cleanup_db, currency):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1000,
                "currency": currency,
                "merchant_id": f"TEST_MERCHANT_{currency}",
                "order_reference": f"ORDER_{currency}",
                "country_code": "CL",
            },
        )
        assert response.status_code == 201

    def test_create_capture_success(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 5000,
                "currency": "USD",
                "merchant_id": "TEST_MERCHANT_002",
                "order_reference": "ORDER_002",
                "country_code": "US",
            },
        )
        auth_id = auth_response.get_json()["id"]

        response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 5000,
                "currency": "USD",
                "merchant_id": "TEST_MERCHANT_002",
                "order_reference": "ORDER_003",
                "country_code": "US",
                "parent_id": auth_id,
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "PENDING"

    def test_create_refund_success(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 3000,
                "currency": "EUR",
                "merchant_id": "TEST_MERCHANT_003",
                "order_reference": "ORDER_004",
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
                "merchant_id": "TEST_MERCHANT_003",
                "order_reference": "ORDER_005",
                "country_code": "ES",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 1000,
                "currency": "EUR",
                "merchant_id": "TEST_MERCHANT_003",
                "order_reference": "ORDER_006",
                "country_code": "ES",
                "parent_id": capture_id,
            },
        )
        assert response.status_code == 201

    def test_idempotency(self, client, cleanup_db):
        payload = {
            "type": "AUTH",
            "amount": 1000,
            "currency": "CLP",
            "merchant_id": "TEST_MERCHANT_004",
            "order_reference": "IDEMPOTENT_001",
            "country_code": "CL",
        }

        response1 = client.post("/transactions", json=payload)
        assert response1.status_code == 201
        txn_id_1 = response1.get_json()["id"]

        response2 = client.post("/transactions", json=payload)
        assert response2.status_code == 200
        data2 = response2.get_json()
        assert data2["message"] == "transaction already exists"
        assert data2["id"] == txn_id_1

    def test_idempotency_with_metadata(self, client, cleanup_db):
        payload = {
            "type": "AUTH",
            "amount": 1500,
            "currency": "USD",
            "merchant_id": "TEST_MERCHANT_IDEM_META",
            "order_reference": "IDEMPOTENT_META_001",
            "country_code": "US",
            "metadata": {"session_id": "sess_12345", "user_agent": "Mozilla/5.0"},
        }

        response1 = client.post("/transactions", json=payload)
        assert response1.status_code == 201
        txn_id_1 = response1.get_json()["id"]

        response2 = client.post("/transactions", json=payload)
        assert response2.status_code == 200
        data2 = response2.get_json()
        assert data2["id"] == txn_id_1

        get_response = client.get(f"/transactions/{txn_id_1}")
        txn = get_response.get_json()
        assert txn["metadata"]["session_id"] == "sess_12345"

    @pytest.mark.parametrize("idx,amount", enumerate([100.00, 0.01]))
    def test_create_with_decimal_amount(self, client, cleanup_db, idx, amount):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": amount,
                "currency": "USD",
                "merchant_id": f"TEST_MERCHANT_D{idx}",
                "order_reference": f"ORDER_DECIMAL_{idx}",
                "country_code": "US",
            },
        )
        assert response.status_code == 201
