import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.catalog.models import Category, Choice, Question


class QuizSession(models.Model):
    RANKING_ORDER = ("-score", "total_answer_ms", "finished_at")

    class Status(models.TextChoices):
        ACTIVE = "active", "Aktif"
        FINISHED = "finished", "Bitti"
        EXPIRED = "expired", "Süresi Doldu"

    class Platform(models.TextChoices):
        WEB = "web", "Web"
        IOS = "ios", "iOS"
        ANDROID = "android", "Android"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="sessions")
    question_ids = ArrayField(models.PositiveBigIntegerField())
    current_index = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    total_answer_ms = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    player_name = models.CharField(max_length=20, null=True, blank=True)
    is_hidden = models.BooleanField(default=False)
    platform = models.CharField(max_length=7, choices=Platform.choices, default=Platform.WEB)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "status", "-score", "total_answer_ms"]),
        ]

    def __str__(self):
        return str(self.id)


class SessionAnswer(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    shown_at = models.DateTimeField()
    answered_at = models.DateTimeField(null=True, blank=True)
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    points = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "question"], name="unique_session_question"),
        ]
