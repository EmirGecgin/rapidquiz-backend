from datetime import timedelta

from django.utils import timezone

from apps.catalog.models import Choice
from tests.conftest import frozen_time, start_session


def _serve_question(api_client, headers, session_url, at):
    with frozen_time(at):
        response = api_client.post(f"{session_url}/next/", format="json", **headers)
    return response.json()


def test_correct_answer_fast_awards_fourteen_points(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    question = _serve_question(api_client, headers, session_url, t0)
    correct_choice_id = Choice.objects.get(question_id=question["question_id"], is_correct=True).id

    with frozen_time(t0 + timedelta(milliseconds=500)):
        response = api_client.post(
            f"{session_url}/answer/",
            {"question_id": question["question_id"], "choice_id": correct_choice_id},
            format="json",
            **headers,
        )

    data = response.json()
    assert data["is_correct"] is True
    assert data["points"] == 14
    assert data["score"] == 14


def test_correct_answer_slow_awards_ten_points(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    question = _serve_question(api_client, headers, session_url, t0)
    correct_choice_id = Choice.objects.get(question_id=question["question_id"], is_correct=True).id

    with frozen_time(t0 + timedelta(milliseconds=4900)):
        response = api_client.post(
            f"{session_url}/answer/",
            {"question_id": question["question_id"], "choice_id": correct_choice_id},
            format="json",
            **headers,
        )

    data = response.json()
    assert data["points"] == 10
    assert data["score"] == 10


def test_wrong_answer_awards_minus_five_points(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    question = _serve_question(api_client, headers, session_url, t0)
    wrong_choice_id = Choice.objects.filter(question_id=question["question_id"], is_correct=False).first().id

    with frozen_time(t0 + timedelta(milliseconds=1000)):
        response = api_client.post(
            f"{session_url}/answer/",
            {"question_id": question["question_id"], "choice_id": wrong_choice_id},
            format="json",
            **headers,
        )

    data = response.json()
    assert data["is_correct"] is False
    assert data["points"] == -5
    assert data["score"] == 0


def test_timeout_answer_awards_minus_five_points(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    question = _serve_question(api_client, headers, session_url, t0)
    correct_choice_id = Choice.objects.get(question_id=question["question_id"], is_correct=True).id

    with frozen_time(t0 + timedelta(milliseconds=5900)):
        response = api_client.post(
            f"{session_url}/answer/",
            {"question_id": question["question_id"], "choice_id": correct_choice_id},
            format="json",
            **headers,
        )

    data = response.json()
    assert data["is_correct"] is False
    assert data["points"] == -5


def test_score_never_goes_below_zero(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    question = _serve_question(api_client, headers, session_url, t0)
    wrong_choice_id = Choice.objects.filter(question_id=question["question_id"], is_correct=False).first().id

    with frozen_time(t0 + timedelta(milliseconds=1000)):
        response = api_client.post(
            f"{session_url}/answer/",
            {"question_id": question["question_id"], "choice_id": wrong_choice_id},
            format="json",
            **headers,
        )

    assert response.json()["score"] == 0
