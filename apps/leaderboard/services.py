from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.catalog.models import Category
from apps.game.models import QuizSession

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
PERIOD_CHOICES = ("day", "week", "all")


def period_start(period):
    if period == "all":
        return None

    now_local = timezone.localtime(timezone.now())
    start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "day":
        return start_of_day
    if period == "week":
        return start_of_day - timedelta(days=start_of_day.weekday())

    raise ValueError(f"Geçersiz period: {period!r}")


def get_leaderboard(category_slug, period, limit):
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    start = period_start(period)

    queryset = (
        QuizSession.objects.filter(category=category, status=QuizSession.Status.FINISHED, is_hidden=False)
        .exclude(player_name__isnull=True)
        .exclude(player_name="")
    )
    if start is not None:
        queryset = queryset.filter(finished_at__gte=start)

    entries = list(queryset.order_by(*QuizSession.RANKING_ORDER)[:limit])

    return [
        {
            "rank": index + 1,
            "player_name": session.player_name,
            "score": session.score,
            "correct_count": session.correct_count,
            "finished_at": session.finished_at,
        }
        for index, session in enumerate(entries)
    ]
