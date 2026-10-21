from django.core.exceptions import ValidationError
from django.db import models


def validate_choice_set(choices):
    if len(choices) != 4:
        raise ValidationError("Her soruda tam 4 şık olmalı.")
    correct_count = sum(1 for choice in choices if choice.is_correct)
    if correct_count != 1:
        raise ValidationError("Her soruda tam 1 doğru şık olmalı.")


class Category(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=60, unique=True)
    icon = models.CharField(max_length=40)
    color = models.CharField(max_length=7)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Kolay"
        MEDIUM = "medium", "Orta"
        HARD = "hard", "Zor"

    category = models.ForeignKey(Category, related_name="questions", on_delete=models.CASCADE)
    text = models.CharField(max_length=140)
    difficulty = models.CharField(max_length=6, choices=Difficulty.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

    def clean(self):
        if self.pk:
            validate_choice_set(list(self.choices.all()))


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=30)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text
