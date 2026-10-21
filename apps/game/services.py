import random
import re
import secrets

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Category, Choice, Question

from .exceptions import AlreadyAnswered, InvalidName, InvalidToken, QuestionMismatch, SessionExpired, SessionFinished
from .models import QuizSession, SessionAnswer

TOTAL_QUESTIONS = 10
DIFFICULTY_TARGETS = {"easy": 4, "medium": 4, "hard": 2}
TIME_LIMIT_MS = 5000
GRACE_MS = 5800
PENALTY_POINTS = -5
BASE_POINTS = 10
MAX_SPEED_BONUS = 4
NAME_PATTERN = re.compile(r"^[A-Za-zÇĞİÖŞÜçğıöşü0-9 _.-]+$")


def _select_question_ids(category):
    pools = {
        difficulty: list(
            Question.objects.filter(
                category=category, difficulty=difficulty, is_active=True
            ).values_list("id", flat=True)
        )
        for difficulty in DIFFICULTY_TARGETS
    }
    for pool in pools.values():
        random.shuffle(pool)

    selected = []
    leftovers = []
    for difficulty, target in DIFFICULTY_TARGETS.items():
        pool = pools[difficulty]
        selected.extend(pool[:target])
        leftovers.extend(pool[target:])

    random.shuffle(leftovers)
    if len(selected) < TOTAL_QUESTIONS:
        selected.extend(leftovers[: TOTAL_QUESTIONS - len(selected)])

    random.shuffle(selected)
    return selected[:TOTAL_QUESTIONS]


def start_session(category_slug, platform):
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    question_ids = _select_question_ids(category)

    return QuizSession.objects.create(
        token=secrets.token_urlsafe(48),
        category=category,
        question_ids=question_ids,
        platform=platform,
    )


def get_authenticated_session(session_id, token):
    session = get_object_or_404(QuizSession, pk=session_id)
    if not token or not secrets.compare_digest(token, session.token):
        raise InvalidToken()
    if session.status == QuizSession.Status.EXPIRED:
        raise SessionExpired()
    return session


def _require_active(session):
    if session.status == QuizSession.Status.FINISHED:
        raise SessionFinished()


def _score_answer(session, session_answer, choice, now):
    elapsed_ms = int((now - session_answer.shown_at).total_seconds() * 1000)
    timed_out = choice is None or elapsed_ms > GRACE_MS

    if timed_out:
        is_correct = False
        points = PENALTY_POINTS
        chosen_choice = None
    else:
        chosen_choice = choice
        is_correct = choice.is_correct
        if is_correct:
            bonus = min(MAX_SPEED_BONUS, (TIME_LIMIT_MS - min(elapsed_ms, TIME_LIMIT_MS)) // 1000)
            points = BASE_POINTS + bonus
        else:
            points = PENALTY_POINTS

    session_answer.answered_at = now
    session_answer.choice = chosen_choice
    session_answer.is_correct = is_correct
    session_answer.points = points
    session_answer.save()

    capped_elapsed = min(elapsed_ms, TIME_LIMIT_MS)
    session.total_answer_ms += capped_elapsed
    session.score = max(0, session.score + points)
    if is_correct:
        session.correct_count += 1
    session.save(update_fields=["total_answer_ms", "score", "correct_count"])

    return capped_elapsed


def _close_previous_if_pending(session, now):
    if session.current_index == 0:
        return

    previous_question_id = session.question_ids[session.current_index - 1]
    pending = SessionAnswer.objects.filter(
        session=session, question_id=previous_question_id, answered_at__isnull=True
    ).first()
    if pending is None:
        return

    _score_answer(session, pending, choice=None, now=now)


def next_question(session, now=None):
    now = now or timezone.now()
    _require_active(session)
    _close_previous_if_pending(session, now)

    if session.current_index >= len(session.question_ids):
        return {"done": True}

    question_id = session.question_ids[session.current_index]
    question = Question.objects.prefetch_related("choices").get(pk=question_id)

    SessionAnswer.objects.create(session=session, question=question, shown_at=now)

    session.current_index += 1
    session.save(update_fields=["current_index"])

    choices = list(question.choices.all())
    random.shuffle(choices)

    return {
        "index": session.current_index - 1,
        "question_id": question.id,
        "text": question.text,
        "choices": [{"id": choice.id, "text": choice.text} for choice in choices],
        "time_limit_ms": TIME_LIMIT_MS,
    }


def submit_answer(session, question_id, choice_id, now=None):
    now = now or timezone.now()
    _require_active(session)

    try:
        session_answer = SessionAnswer.objects.get(session=session, question_id=question_id)
    except SessionAnswer.DoesNotExist:
        raise QuestionMismatch()

    if session_answer.answered_at is not None:
        raise AlreadyAnswered()

    choice = None
    if choice_id is not None:
        try:
            choice = Choice.objects.get(pk=choice_id, question_id=question_id)
        except Choice.DoesNotExist:
            raise ValidationError({"choice_id": "Geçersiz şık."})

    elapsed_ms = _score_answer(session, session_answer, choice, now)

    correct_choice = Choice.objects.get(question_id=question_id, is_correct=True)

    return {
        "is_correct": session_answer.is_correct,
        "correct_choice_id": correct_choice.id,
        "points": session_answer.points,
        "score": session.score,
        "elapsed_ms": elapsed_ms,
    }


def finish_session(session, player_name, now=None):
    now = now or timezone.now()
    _require_active(session)

    if session.current_index < len(session.question_ids):
        raise ValidationError("Tur henüz bitmedi.")

    name = (player_name or "").strip()
    if not (2 <= len(name) <= 20) or not NAME_PATTERN.match(name):
        raise InvalidName()

    session.player_name = name
    session.status = QuizSession.Status.FINISHED
    session.finished_at = now
    session.save(update_fields=["player_name", "status", "finished_at"])

    return {
        "score": session.score,
        "rank": compute_rank(session),
        "correct_count": session.correct_count,
    }


def compute_rank(session):
    better_count = (
        QuizSession.objects.filter(category=session.category, status=QuizSession.Status.FINISHED, is_hidden=False)
        .exclude(pk=session.pk)
        .filter(
            Q(score__gt=session.score)
            | Q(score=session.score, total_answer_ms__lt=session.total_answer_ms)
            | Q(
                score=session.score,
                total_answer_ms=session.total_answer_ms,
                finished_at__lt=session.finished_at,
            )
        )
        .count()
    )
    return better_count + 1
