from contextlib import contextmanager
from unittest import mock

import pytest
from rest_framework.test import APIClient

from apps.catalog.models import Category, Choice, Question


@pytest.fixture
def category(db):
    category = Category.objects.create(name="Tarih", slug="tarih", icon="landmark", color="#E8B4A0", order=5)
    for difficulty, count in (("easy", 4), ("medium", 4), ("hard", 2)):
        for i in range(count):
            question = Question.objects.create(category=category, text=f"{difficulty}-{i}", difficulty=difficulty)
            for choice_index in range(4):
                Choice.objects.create(question=question, text=str(choice_index), is_correct=(choice_index == 0))
    return category


@pytest.fixture
def api_client():
    return APIClient()


def start_session(client, category):
    response = client.post("/api/v1/sessions/", {"category": category.slug, "platform": "web"}, format="json")
    assert response.status_code == 201
    return response.json()


@contextmanager
def frozen_time(dt):
    with mock.patch("apps.game.services.timezone.now", return_value=dt):
        yield
