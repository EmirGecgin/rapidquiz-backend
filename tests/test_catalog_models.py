import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Category, Choice, Question


@pytest.fixture
def category(db):
    return Category.objects.create(name="Tarih", slug="tarih", icon="landmark", color="#E8B4A0", order=5)


def test_question_clean_passes_with_four_choices_one_correct(category):
    question = Question.objects.create(category=category, text="Soru?", difficulty="easy")
    for i in range(4):
        Choice.objects.create(question=question, text=str(i), is_correct=(i == 0))

    question.clean()


def test_question_clean_fails_with_wrong_choice_count(category):
    question = Question.objects.create(category=category, text="Soru?", difficulty="easy")
    for i in range(3):
        Choice.objects.create(question=question, text=str(i), is_correct=(i == 0))

    with pytest.raises(ValidationError):
        question.clean()


def test_question_clean_fails_with_wrong_correct_count(category):
    question = Question.objects.create(category=category, text="Soru?", difficulty="easy")
    for i in range(4):
        Choice.objects.create(question=question, text=str(i), is_correct=True)

    with pytest.raises(ValidationError):
        question.clean()
