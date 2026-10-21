from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

from apps.catalog.models import Choice
from apps.game.models import QuizSession
from apps.game.profanity import contains_profanity
from tests.conftest import frozen_time, start_session


def test_contains_profanity_detects_blocked_words():
    assert contains_profanity("siktir git") is True
    assert contains_profanity("amk") is True
    assert contains_profanity("FuckYou123") is True
    assert contains_profanity("f u c k sen") is True


def test_contains_profanity_allows_clean_names():
    assert contains_profanity("Ahmet Yılmaz") is False
    assert contains_profanity("Oyuncu_42") is False


def test_throttle_rates_match_spec():
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    assert rates["session_create"] == "10/min"
    assert rates["answer_submit"] == "120/min"


def test_session_create_is_throttled_after_ten_per_minute(api_client, category):
    for _ in range(10):
        response = api_client.post(
            "/api/v1/sessions/", {"category": category.slug, "platform": "web"}, format="json"
        )
        assert response.status_code == 201

    response = api_client.post("/api/v1/sessions/", {"category": category.slug, "platform": "web"}, format="json")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"


def test_expire_sessions_marks_old_active_sessions_as_expired(category):
    old_session = QuizSession.objects.create(
        token="a" * 64, category=category, question_ids=[1, 2, 3], status=QuizSession.Status.ACTIVE
    )
    QuizSession.objects.filter(pk=old_session.pk).update(created_at=timezone.now() - timedelta(minutes=11))

    recent_session = QuizSession.objects.create(
        token="b" * 64, category=category, question_ids=[1, 2, 3], status=QuizSession.Status.ACTIVE
    )

    call_command("expire_sessions")

    old_session.refresh_from_db()
    recent_session.refresh_from_db()

    assert old_session.status == QuizSession.Status.EXPIRED
    assert recent_session.status == QuizSession.Status.ACTIVE


def test_expire_sessions_does_not_touch_finished_sessions(category):
    finished = QuizSession.objects.create(
        token="c" * 64, category=category, question_ids=[1], status=QuizSession.Status.FINISHED
    )
    QuizSession.objects.filter(pk=finished.pk).update(created_at=timezone.now() - timedelta(minutes=20))

    call_command("expire_sessions")

    finished.refresh_from_db()
    assert finished.status == QuizSession.Status.FINISHED


def test_finish_rejects_profane_player_name(api_client, category):
    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    for i in range(10):
        with frozen_time(t0 + timedelta(seconds=i * 6)):
            next_response = api_client.post(f"{session_url}/next/", format="json", **headers)
        question = next_response.json()
        correct_choice_id = Choice.objects.get(question_id=question["question_id"], is_correct=True).id
        with frozen_time(t0 + timedelta(seconds=i * 6, milliseconds=500)):
            api_client.post(
                f"{session_url}/answer/",
                {"question_id": question["question_id"], "choice_id": correct_choice_id},
                format="json",
                **headers,
            )

    with frozen_time(t0 + timedelta(seconds=100)):
        response = api_client.post(f"{session_url}/finish/", {"player_name": "amk"}, format="json", **headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_name"


def test_expired_session_rejects_next_with_session_expired(api_client, category):
    session_data = start_session(api_client, category)
    QuizSession.objects.filter(pk=session_data["session_id"]).update(
        created_at=timezone.now() - timedelta(minutes=11)
    )

    call_command("expire_sessions")

    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    response = api_client.post(f"/api/v1/sessions/{session_data['session_id']}/next/", format="json", **headers)

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "session_expired"
