class TestHTTPStatusCodes:
    """test http status codes"""

    def test_404_invalid_endpoint(self, client):
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404
        assert "error" in response.get_json()

    def test_405_method_not_allowed(self, client):
        response = client.put("/transactions")
        assert response.status_code == 405
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "method not allowed"

    def test_400_malformed_json(self, client):
        response = client.post(
            "/transactions",
            data="{invalid json}",
            content_type="application/json",
        )
        assert response.status_code == 400
