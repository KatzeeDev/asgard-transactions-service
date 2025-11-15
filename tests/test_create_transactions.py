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

        txn_id = data["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        assert get_response.status_code == 200
        txn = get_response.get_json()

        assert txn["id"] == txn_id
        assert txn["type"] == "AUTH"
        assert txn["amount"] == "10000.50"
        assert txn["currency"] == "CLP"
        assert txn["merchant_id"] == "TEST_MERCHANT_001"
        assert txn["order_reference"] == "ORDER_001"
        assert txn["country_code"] == "CL"
        assert txn["status"] == "PENDING"
        assert txn.get("parent_id") is None
        assert "created_at" in txn
        assert "status_updated_at" in txn

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

        txn_id = response.get_json()["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["metadata"] is not None
        assert txn["metadata"]["customer_email"] == "test@example.com"
        assert txn["metadata"]["customer_name"] == "John Doe"
        assert txn["metadata"]["device"] == "mobile"
        assert txn["metadata"]["ip_address"] == "192.168.1.1"
        assert txn["metadata"]["cart_items"] == ["item1", "item2"]

    def test_create_auth_with_error_code(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 2500,
                "currency": "EUR",
                "merchant_id": "TEST_MERCHANT_ERROR",
                "order_reference": "ORDER_ERROR_001",
                "country_code": "ES",
                "error_code": "INSUFFICIENT_FUNDS",
            },
        )
        assert response.status_code == 201

        txn_id = response.get_json()["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["error_code"] == "INSUFFICIENT_FUNDS"
        assert txn["status"] == "PENDING"

    def test_create_auth_all_currencies(self, client, cleanup_db):
        currencies = ["CLP", "USD", "EUR", "GBP"]

        for currency in currencies:
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

            txn_id = response.get_json()["id"]
            get_response = client.get(f"/transactions/{txn_id}")
            txn = get_response.get_json()
            assert txn["currency"] == currency

    def test_create_auth_all_countries(self, client, cleanup_db):
        countries = ["CL", "US", "ES", "GB", "SE", "BR", "AR", "MX", "CO", "PE", "UY"]

        for country in countries:
            response = client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": 500,
                    "currency": "USD",
                    "merchant_id": f"TEST_MERCHANT_{country}",
                    "order_reference": f"ORDER_{country}",
                    "country_code": country,
                },
            )
            assert response.status_code == 201

            txn_id = response.get_json()["id"]
            get_response = client.get(f"/transactions/{txn_id}")
            txn = get_response.get_json()
            assert txn["country_code"] == country

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

        txn_id = data["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["type"] == "CAPTURE"
        assert txn["parent_id"] == auth_id
        assert "created_at" in txn
        assert "status_updated_at" in txn

    def test_create_capture_with_metadata(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 3000,
                "currency": "EUR",
                "merchant_id": "TEST_MERCHANT_CAP_META",
                "order_reference": "ORDER_CAP_META_001",
                "country_code": "ES",
            },
        )
        auth_id = auth_response.get_json()["id"]

        response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 3000,
                "currency": "EUR",
                "merchant_id": "TEST_MERCHANT_CAP_META",
                "order_reference": "ORDER_CAP_META_002",
                "country_code": "ES",
                "parent_id": auth_id,
                "metadata": {
                    "capture_reason": "customer_confirmed",
                    "processed_by": "automated_system",
                },
            },
        )
        assert response.status_code == 201

        txn_id = response.get_json()["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["metadata"]["capture_reason"] == "customer_confirmed"
        assert txn["metadata"]["processed_by"] == "automated_system"

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

        txn_id = response.get_json()["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["type"] == "REFUND"
        assert txn["parent_id"] == capture_id
        assert txn["amount"] == "1000.00"

    def test_create_refund_with_metadata_and_error_code(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 8000,
                "currency": "GBP",
                "merchant_id": "TEST_MERCHANT_REF_META",
                "order_reference": "ORDER_REF_META_001",
                "country_code": "GB",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 8000,
                "currency": "GBP",
                "merchant_id": "TEST_MERCHANT_REF_META",
                "order_reference": "ORDER_REF_META_002",
                "country_code": "GB",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 2000,
                "currency": "GBP",
                "merchant_id": "TEST_MERCHANT_REF_META",
                "order_reference": "ORDER_REF_META_003",
                "country_code": "GB",
                "parent_id": capture_id,
                "metadata": {
                    "refund_reason": "customer_request",
                    "customer_email": "customer@example.com",
                    "refund_method": "original_payment",
                },
                "error_code": "PARTIAL_REFUND",
            },
        )
        assert response.status_code == 201

        txn_id = response.get_json()["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["metadata"]["refund_reason"] == "customer_request"
        assert txn["metadata"]["customer_email"] == "customer@example.com"
        assert txn["metadata"]["refund_method"] == "original_payment"
        assert txn["error_code"] == "PARTIAL_REFUND"

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

    def test_create_with_decimal_amounts(self, client, cleanup_db):
        amounts = [100.00, 999.99, 10000.50, 0.01, 9999999999.99]

        for idx, amount in enumerate(amounts):
            response = client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": amount,
                    "currency": "USD",
                    "merchant_id": f"TEST_MERCHANT_DECIMAL_{idx}",
                    "order_reference": f"ORDER_DECIMAL_{idx}",
                    "country_code": "US",
                },
            )
            assert response.status_code == 201

            txn_id = response.get_json()["id"]
            get_response = client.get(f"/transactions/{txn_id}")
            txn = get_response.get_json()
            assert float(txn["amount"]) == amount

    def test_create_with_complex_metadata(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 7500,
                "currency": "EUR",
                "merchant_id": "TEST_MERCHANT_COMPLEX_META",
                "order_reference": "ORDER_COMPLEX_META",
                "country_code": "ES",
                "metadata": {
                    "customer": {
                        "id": "cust_12345",
                        "email": "customer@example.com",
                        "name": "Jane Smith",
                    },
                    "shipping": {
                        "address": "123 Main St",
                        "city": "Madrid",
                        "postal_code": "28001",
                    },
                    "items": [
                        {"sku": "PROD-001", "quantity": 2, "price": 2500},
                        {"sku": "PROD-002", "quantity": 1, "price": 2500},
                    ],
                    "total_items": 3,
                },
            },
        )
        assert response.status_code == 201

        txn_id = response.get_json()["id"]
        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()

        assert txn["metadata"]["customer"]["email"] == "customer@example.com"
        assert txn["metadata"]["shipping"]["city"] == "Madrid"
        assert len(txn["metadata"]["items"]) == 2
        assert txn["metadata"]["total_items"] == 3

    def test_create_different_error_codes(self, client, cleanup_db):
        error_codes = [
            "INSUFFICIENT_FUNDS",
            "CARD_EXPIRED",
            "INVALID_CARD",
            "DECLINED_BY_ISSUER",
            "NETWORK_ERROR",
            "FRAUD_SUSPECTED",
        ]

        for idx, error_code in enumerate(error_codes):
            response = client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": 1000,
                    "currency": "CLP",
                    "merchant_id": f"TEST_MERCHANT_ERR_{idx}",
                    "order_reference": f"ORDER_ERR_{idx}",
                    "country_code": "CL",
                    "error_code": error_code,
                },
            )
            assert response.status_code == 201

            txn_id = response.get_json()["id"]
            get_response = client.get(f"/transactions/{txn_id}")
            txn = get_response.get_json()
            assert txn["error_code"] == error_code
