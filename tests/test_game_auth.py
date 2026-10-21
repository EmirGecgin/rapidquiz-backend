from tests.conftest import start_session


def test_next_with_wrong_token_is_rejected(api_client, category):
    session_data = start_session(api_client, category)
    session_url = f"/api/v1/sessions/{session_data['session_id']}"

    response = api_client.post(f"{session_url}/next/", format="json", HTTP_X_SESSION_TOKEN="wrong-token")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_answer_with_unknown_question_id_is_question_mismatch(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"

    api_client.post(f"{session_url}/next/", format="json", **headers)

    response = api_client.post(
        f"{session_url}/answer/", {"question_id": 999999, "choice_id": None}, format="json", **headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "question_mismatch"
