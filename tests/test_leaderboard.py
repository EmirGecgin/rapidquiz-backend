from datetime import timedelta

from django.utils import timezone

from apps.catalog.models import Choice
from apps.game.models import QuizSession
from tests.conftest import frozen_time, start_session


def _finished_session(
    category,
    score,
    total_answer_ms,
    finished_at,
    player_name="Oyuncu",
    is_hidden=False,
    status=QuizSession.Status.FINISHED,
):
    return QuizSession.objects.create(
        token="x" * 64,
        category=category,
        question_ids=[],
        score=score,
        total_answer_ms=total_answer_ms,
        status=status,
        player_name=player_name,
        is_hidden=is_hidden,
        finished_at=finished_at,
    )


def test_leaderboard_orders_by_score_desc_time_asc_finished_asc(api_client, category):
    now = timezone.now()
    _finished_session(category, score=100, total_answer_ms=5000, finished_at=now, player_name="Orta")
    _finished_session(category, score=140, total_answer_ms=3000, finished_at=now, player_name="Birinci")
    _finished_session(category, score=100, total_answer_ms=4000, finished_at=now, player_name="İkinci")

    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/")

    assert response.status_code == 200
    data = response.json()
    assert [entry["player_name"] for entry in data] == ["Birinci", "İkinci", "Orta"]
    assert [entry["rank"] for entry in data] == [1, 2, 3]


def test_leaderboard_excludes_unfinished_hidden_and_unnamed(api_client, category):
    now = timezone.now()
    _finished_session(category, score=100, total_answer_ms=1000, finished_at=now, status=QuizSession.Status.ACTIVE)
    _finished_session(category, score=100, total_answer_ms=1000, finished_at=now, is_hidden=True)
    _finished_session(category, score=100, total_answer_ms=1000, finished_at=now, player_name=None)
    _finished_session(category, score=100, total_answer_ms=1000, finished_at=now, player_name="Görünen")

    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/")

    data = response.json()
    assert len(data) == 1
    assert data[0]["player_name"] == "Görünen"


def test_leaderboard_period_day_excludes_older_entries(api_client, category):
    now_local = timezone.localtime(timezone.now())
    yesterday = now_local.replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(days=1)

    _finished_session(category, score=100, total_answer_ms=1000, finished_at=yesterday, player_name="Dün")
    _finished_session(category, score=100, total_answer_ms=1000, finished_at=now_local, player_name="Bugün")

    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/?period=day")

    data = response.json()
    assert [entry["player_name"] for entry in data] == ["Bugün"]


def test_leaderboard_period_week_excludes_entries_before_this_week(api_client, category):
    now_local = timezone.localtime(timezone.now())
    last_week = now_local.replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(days=now_local.weekday() + 1)

    _finished_session(category, score=100, total_answer_ms=1000, finished_at=last_week, player_name="GecenHafta")
    _finished_session(category, score=100, total_answer_ms=1000, finished_at=now_local, player_name="BuHafta")

    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/?period=week")

    data = response.json()
    assert [entry["player_name"] for entry in data] == ["BuHafta"]


def test_leaderboard_respects_limit(api_client, category):
    now = timezone.now()
    for i in range(5):
        _finished_session(category, score=100 - i, total_answer_ms=1000, finished_at=now, player_name=f"P{i}")

    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/?limit=2")

    assert len(response.json()) == 2


def test_leaderboard_rejects_invalid_period(api_client, category):
    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/?period=month")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_leaderboard_rejects_limit_over_100(api_client, category):
    response = api_client.get(f"/api/v1/leaderboard/{category.slug}/?limit=101")

    assert response.status_code == 400


def test_finish_rank_matches_leaderboard_position(api_client, category):
    now = timezone.now()
    _finished_session(category, score=140, total_answer_ms=1000, finished_at=now, player_name="Lider")

    session_data = start_session(api_client, category)
    headers = {"HTTP_X_SESSION_TOKEN": session_data["token"]}
    session_url = f"/api/v1/sessions/{session_data['session_id']}"
    t0 = timezone.now()

    for i in range(10):
        with frozen_time(t0 + timedelta(seconds=i * 6)):
            next_response = api_client.post(f"{session_url}/next/", format="json", **headers)
        question = next_response.json()
        wrong_choice_id = Choice.objects.filter(question_id=question["question_id"], is_correct=False).first().id
        with frozen_time(t0 + timedelta(seconds=i * 6, milliseconds=500)):
            api_client.post(
                f"{session_url}/answer/",
                {"question_id": question["question_id"], "choice_id": wrong_choice_id},
                format="json",
                **headers,
            )

    with frozen_time(t0 + timedelta(seconds=100)):
        finish_response = api_client.post(
            f"{session_url}/finish/", {"player_name": "İkinci"}, format="json", **headers
        )

    assert finish_response.json()["rank"] == 2

    leaderboard_response = api_client.get(f"/api/v1/leaderboard/{category.slug}/")
    names_in_order = [entry["player_name"] for entry in leaderboard_response.json()]
    assert names_in_order == ["Lider", "İkinci"]
