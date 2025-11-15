class TestUpdateTransaction:
    """test status updates"""

    def test_update_status_success(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 200,
                "currency": "CLP",
                "merchant_id": "TEST_UPDATE_001",
                "order_reference": "ORDER_UPDATE_001",
                "country_code": "CL",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "APPROVED"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "APPROVED"

    def test_update_to_processing(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 300,
                "currency": "USD",
                "merchant_id": "TEST_UPDATE_PROC",
                "order_reference": "ORDER_UPDATE_PROC",
                "country_code": "US",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "PROCESSING"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "PROCESSING"
        assert data["id"] == txn_id

    def test_update_to_declined(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 500,
                "currency": "EUR",
                "merchant_id": "TEST_UPDATE_DEC",
                "order_reference": "ORDER_UPDATE_DEC",
                "country_code": "ES",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "DECLINED"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "DECLINED"

        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()
        assert txn["processed_at"] is not None

    def test_update_to_failed(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1000,
                "currency": "GBP",
                "merchant_id": "TEST_UPDATE_FAIL",
                "order_reference": "ORDER_UPDATE_FAIL",
                "country_code": "GB",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "FAILED"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "FAILED"

        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()
        assert txn["processed_at"] is not None

    def test_update_to_expired(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 750,
                "currency": "USD",
                "merchant_id": "TEST_UPDATE_EXP",
                "order_reference": "ORDER_UPDATE_EXP",
                "country_code": "US",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "EXPIRED"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "EXPIRED"

        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()
        assert txn["processed_at"] is not None

    def test_update_to_cancelled(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 900,
                "currency": "CLP",
                "merchant_id": "TEST_UPDATE_CANC",
                "order_reference": "ORDER_UPDATE_CANC",
                "country_code": "CL",
            },
        )
        txn_id = create_response.get_json()["id"]

        response = client.patch(
            f"/transactions/{txn_id}", json={"status": "CANCELLED"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "CANCELLED"

        get_response = client.get(f"/transactions/{txn_id}")
        txn = get_response.get_json()
        assert txn["processed_at"] is not None

    def test_update_all_final_states_have_processed_at(self, client, cleanup_db):
        final_states = ["APPROVED", "DECLINED", "FAILED", "EXPIRED", "CANCELLED"]

        for idx, status in enumerate(final_states):
            create_response = client.post(
                "/transactions",
                json={
                    "type": "AUTH",
                    "amount": 100 + idx,
                    "currency": "USD",
                    "merchant_id": f"TEST_FINAL_{idx}",
                    "order_reference": f"ORDER_FINAL_{idx}",
                    "country_code": "US",
                },
            )
            txn_id = create_response.get_json()["id"]

            update_response = client.patch(
                f"/transactions/{txn_id}", json={"status": status}
            )
            assert update_response.status_code == 200

            get_response = client.get(f"/transactions/{txn_id}")
            txn = get_response.get_json()
            assert txn["status"] == status
            assert txn["processed_at"] is not None
            assert "created_at" in txn
            assert "status_updated_at" in txn

    def test_update_pending_to_processing_to_approved(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 1500,
                "currency": "EUR",
                "merchant_id": "TEST_UPDATE_FLOW",
                "order_reference": "ORDER_UPDATE_FLOW",
                "country_code": "ES",
            },
        )
        txn_id = create_response.get_json()["id"]

        get_initial = client.get(f"/transactions/{txn_id}")
        txn_initial = get_initial.get_json()
        assert txn_initial["status"] == "PENDING"
        assert txn_initial.get("processed_at") is None

        process_response = client.patch(
            f"/transactions/{txn_id}", json={"status": "PROCESSING"}
        )
        assert process_response.status_code == 200

        get_processing = client.get(f"/transactions/{txn_id}")
        txn_processing = get_processing.get_json()
        assert txn_processing["status"] == "PROCESSING"
        assert txn_processing.get("processed_at") is None

        approve_response = client.patch(
            f"/transactions/{txn_id}", json={"status": "APPROVED"}
        )
        assert approve_response.status_code == 200

        get_final = client.get(f"/transactions/{txn_id}")
        txn_final = get_final.get_json()
        assert txn_final["status"] == "APPROVED"
        assert txn_final["processed_at"] is not None

    def test_update_status_updates_status_updated_at(self, client, cleanup_db):
        create_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 800,
                "currency": "GBP",
                "merchant_id": "TEST_UPDATE_TS",
                "order_reference": "ORDER_UPDATE_TS",
                "country_code": "GB",
            },
        )
        txn_id = create_response.get_json()["id"]

        get_initial = client.get(f"/transactions/{txn_id}")
        initial_status_updated_at = get_initial.get_json()["status_updated_at"]

        import time
        time.sleep(0.1)

        client.patch(f"/transactions/{txn_id}", json={"status": "PROCESSING"})

        get_updated = client.get(f"/transactions/{txn_id}")
        updated_status_updated_at = get_updated.get_json()["status_updated_at"]

        assert updated_status_updated_at >= initial_status_updated_at

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

    def test_update_capture_to_approved(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 2000,
                "currency": "USD",
                "merchant_id": "TEST_UPDATE_CAP",
                "order_reference": "ORDER_UPDATE_CAP_AUTH",
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
                "merchant_id": "TEST_UPDATE_CAP",
                "order_reference": "ORDER_UPDATE_CAP_CAP",
                "country_code": "US",
                "parent_id": auth_id,
            },
        )
        capture_id = capture_response.get_json()["id"]

        update_response = client.patch(
            f"/transactions/{capture_id}", json={"status": "APPROVED"}
        )
        assert update_response.status_code == 200

        get_response = client.get(f"/transactions/{capture_id}")
        txn = get_response.get_json()
        assert txn["status"] == "APPROVED"
        assert txn["processed_at"] is not None

    def test_update_refund_to_declined(self, client, cleanup_db):
        auth_response = client.post(
            "/transactions",
            json={
                "type": "AUTH",
                "amount": 3500,
                "currency": "EUR",
                "merchant_id": "TEST_UPDATE_REF",
                "order_reference": "ORDER_UPDATE_REF_AUTH",
                "country_code": "ES",
            },
        )
        auth_id = auth_response.get_json()["id"]

        capture_response = client.post(
            "/transactions",
            json={
                "type": "CAPTURE",
                "amount": 3500,
                "currency": "EUR",
                "merchant_id": "TEST_UPDATE_REF",
                "order_reference": "ORDER_UPDATE_REF_CAP",
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
                "merchant_id": "TEST_UPDATE_REF",
                "order_reference": "ORDER_UPDATE_REF_REF",
                "country_code": "ES",
                "parent_id": capture_id,
            },
        )
        refund_id = refund_response.get_json()["id"]

        update_response = client.patch(
            f"/transactions/{refund_id}", json={"status": "DECLINED"}
        )
        assert update_response.status_code == 200

        get_response = client.get(f"/transactions/{refund_id}")
        txn = get_response.get_json()
        assert txn["status"] == "DECLINED"
        assert txn["processed_at"] is not None
