import json

import pytest
from django.core.management import CommandError, call_command

from apps.catalog.models import Category, Question

FIXTURE = {
    "category": {"slug": "tarih", "name": "Tarih", "icon": "landmark", "color": "#E8B4A0", "order": 5},
    "questions": [
        {
            "text": "İstanbul hangi yılda fethedildi?",
            "difficulty": "easy",
            "choices": ["1453", "1071", "1299", "1517"],
            "answer": 0,
        }
    ],
}


def _write_fixture(tmp_path, data=FIXTURE):
    path = tmp_path / "tarih.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.mark.django_db
def test_load_questions_creates_category_and_questions(tmp_path):
    call_command("load_questions", _write_fixture(tmp_path))

    assert Category.objects.filter(slug="tarih").exists()
    question = Question.objects.get(text=FIXTURE["questions"][0]["text"])
    assert question.choices.count() == 4
    assert question.choices.filter(is_correct=True).count() == 1


@pytest.mark.django_db
def test_load_questions_is_idempotent(tmp_path):
    path = _write_fixture(tmp_path)
    call_command("load_questions", path)
    call_command("load_questions", path)

    assert Question.objects.filter(text=FIXTURE["questions"][0]["text"]).count() == 1


@pytest.mark.django_db
def test_load_questions_dry_run_does_not_persist(tmp_path):
    call_command("load_questions", _write_fixture(tmp_path), "--dry-run")

    assert not Category.objects.filter(slug="tarih").exists()


@pytest.mark.django_db
def test_load_questions_rejects_question_text_over_limit(tmp_path):
    data = json.loads(json.dumps(FIXTURE))
    data["questions"][0]["text"] = "a" * 91

    with pytest.raises(CommandError):
        call_command("load_questions", _write_fixture(tmp_path, data))
