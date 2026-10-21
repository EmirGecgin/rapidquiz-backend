from datetime import timedelta

from django.utils import timezone

from apps.catalog.models import Choice
from apps.game.models import QuizSession, SessionAnswer
from tests.conftest import frozen_time, start_session


def _answer(api_client, headers, session_url, question, choice_id, at):
    with frozen_time(at):
        return api_client.post(
            f"{session_url}/answer/",
            {"question_id": question["question_id"], "choice_id": choice_id},
            format="json",
            **headers,
        )


def _play_full_round(api_client, headers, session_url, t0):
    for i in range(10):
        with frozen_time(t0 + timedelta(seconds=i * 6)):
            next_response = api_client.post(f"{session_url}/next/", format="json", **headers)
        question = next_response.json()
        assert question.get("done") is not True
        correct_choice_id = Choice.objects.get(question_id=question["question_id"], is_correct=True).id
        _answer(
            api_client,
            headers,
            session_url,
            question,
            correct_choice_id,
            t0 + timedelta(seconds=i * 6, milliseconds=500),
        )


def test_duplicate_answer_is_rejected(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    with frozen_time(t0):
        next_response = api_client.post(f"{session_url}/next/", format="json", **headers)
    question = next_response.json()
    correct_choice_id = Choice.objects.get(question_id=question["question_id"], is_correct=True).id

    first = _answer(api_client, headers, session_url, question, correct_choice_id, t0 + timedelta(milliseconds=500))
    assert first.status_code == 200

    second = _answer(api_client, headers, session_url, question, correct_choice_id, t0 + timedelta(milliseconds=800))
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "already_answered"


def test_next_without_answer_closes_previous_as_timeout(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    with frozen_time(t0):
        first_response = api_client.post(f"{session_url}/next/", format="json", **headers)
    first_question_id = first_response.json()["question_id"]

    with frozen_time(t0 + timedelta(seconds=7)):
        api_client.post(f"{session_url}/next/", format="json", **headers)

    session = QuizSession.objects.get(pk=session_data["session_id"])
    closed_answer = SessionAnswer.objects.get(session=session, question_id=first_question_id)

    assert closed_answer.answered_at is not None
    assert closed_answer.choice_id is None
    assert closed_answer.points == -5
    assert session.score == 0


def test_next_returns_done_after_ten_questions(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    _play_full_round(api_client, headers, session_url, t0)

    with frozen_time(t0 + timedelta(seconds=100)):
        response = api_client.post(f"{session_url}/next/", format="json", **headers)

    assert response.json() == {"done": True}


def test_finish_rejected_when_round_not_complete(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    with frozen_time(t0):
        api_client.post(f"{session_url}/next/", format="json", **headers)

    with frozen_time(t0 + timedelta(seconds=1)):
        response = api_client.post(f"{session_url}/finish/", {"player_name": "Test"}, format="json", **headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_finish_after_full_round_returns_score_rank_and_correct_count(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    _play_full_round(api_client, headers, session_url, t0)

    with frozen_time(t0 + timedelta(seconds=100)):
        response = api_client.post(
            f"{session_url}/finish/", {"player_name": "Test Oyuncu"}, format="json", **headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["correct_count"] == 10
    assert data["score"] == 140
    assert data["rank"] == 1
