def test_preflight_allows_x_session_token_header(client):
    response = client.options(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000000/next/",
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-session-token",
    )

    assert response.status_code == 200
    allowed_headers = response["Access-Control-Allow-Headers"].lower()
    assert "x-session-token" in allowed_headers
