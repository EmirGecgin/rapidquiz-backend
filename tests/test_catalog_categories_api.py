import pytest

from apps.catalog.models import Category, Choice, Question


@pytest.mark.django_db
def test_categories_list_returns_active_categories_with_question_count(client):
    category = Category.objects.create(name="Tarih", slug="tarih", icon="landmark", color="#E8B4A0", order=5)
    Category.objects.create(name="Eski", slug="eski", icon="x", color="#000000", order=9, is_active=False)

    question = Question.objects.create(category=category, text="Soru?", difficulty="easy")
    for i in range(4):
        Choice.objects.create(question=question, text=str(i), is_correct=(i == 0))

    response = client.get("/api/v1/categories/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "tarih"
    assert data[0]["question_count"] == 1


@pytest.mark.django_db
def test_categories_list_excludes_inactive_questions_from_count(client):
    category = Category.objects.create(name="Tarih", slug="tarih", icon="landmark", color="#E8B4A0", order=5)
    Question.objects.create(category=category, text="Aktif soru", difficulty="easy")
    Question.objects.create(category=category, text="Pasif soru", difficulty="easy", is_active=False)

    response = client.get("/api/v1/categories/")

    data = response.json()
    assert data[0]["question_count"] == 1
