class TestBusinessLogic:
    """test business rules enforcement"""

    def test_capture_requires_parent(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_001",
                "order_reference": "ORDER_BIZ_001",
                "country_code": "CL",
            },
        )
        assert response.status_code == 400
        assert "CAPTURE requires parent_id" in response.get_json()["error"]

    def test_refund_requires_parent(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_002",
                "order_reference": "ORDER_BIZ_002",
                "country_code": "CL",
            },
        )
        assert response.status_code == 400
        assert "REFUND requires parent_id" in response.get_json()["error"]

    def test_auth_cannot_have_parent(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_003",
                "order_reference": "ORDER_BIZ_003",
                "country_code": "CL",
                "parent_id": "FAKE_PARENT",
            },
        )
        assert response.status_code == 400
        assert "auth cannot have parent_id" in response.get_json()["error"]

    def test_capture_must_reference_auth(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_004",
                "order_reference": "ORDER_BIZ_004",
                "country_code": "CL",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_004",
                "order_reference": "ORDER_BIZ_005",
                "country_code": "CL",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 100,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_004",
                "order_reference": "ORDER_BIZ_006",
                "country_code": "CL",
                "parent_id": capture_id,
            },
        )
        assert response.status_code == 400
        assert "capture must reference an auth" in response.get_json()["error"]

    def test_refund_can_reference_capture(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 800,
                "currency": "EUR",
                "merchant_id": "TEST_BIZ_REF_CAP",
                "order_reference": "ORDER_BIZ_REF_CAP_AUTH",
                "country_code": "ES",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 800,
                "currency": "EUR",
                "merchant_id": "TEST_BIZ_REF_CAP",
                "order_reference": "ORDER_BIZ_REF_CAP_CAP",
                "country_code": "ES",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        refund_response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 300,
                "currency": "EUR",
                "merchant_id": "TEST_BIZ_REF_CAP",
                "order_reference": "ORDER_BIZ_REF_CAP_REF",
                "country_code": "ES",
                "parent_id": capture_id,
            },
        )
        assert refund_response.status_code == 201

    def test_refund_cannot_reference_refund(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1000,
                "currency": "GBP",
                "merchant_id": "TEST_BIZ_REF_REF",
                "order_reference": "ORDER_BIZ_REF_REF_AUTH",
                "country_code": "GB",
            },
        )
        auth_id = auth_response.get_json()["id"]

        refund1_response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 200,
                "currency": "GBP",
                "merchant_id": "TEST_BIZ_REF_REF",
                "order_reference": "ORDER_BIZ_REF_REF_REF1",
                "country_code": "GB",
                "parent_id": auth_id,
            },
        )
        refund1_id = refund1_response.get_json()["id"]

        refund2_response = client.post(
            "/transactions",
            json={
                "type": "REFUND",
                "amount": 100,
                "currency": "GBP",
                "merchant_id": "TEST_BIZ_REF_REF",
                "order_reference": "ORDER_BIZ_REF_REF_REF2",
                "country_code": "GB",
                "parent_id": refund1_id,
            },
        )
        assert refund2_response.status_code == 400
        assert (
            "refund must reference auth or capture"
            in refund2_response.get_json()["error"]
        )

    def test_parent_not_found(self, client, cleanup_db):
        response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 500,
                "currency": "CLP",
                "merchant_id": "TEST_BIZ_NO_PARENT",
                "order_reference": "ORDER_BIZ_NO_PARENT",
                "country_code": "CL",
                "parent_id": "NONEXISTENT_PARENT_ID",
            },
        )
        assert response.status_code == 400
        assert "parent transaction not found" in response.get_json()["error"]
