import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Category, Choice, Question

MAX_QUESTION_TEXT_LENGTH = 90
MAX_CHOICE_TEXT_LENGTH = 30
CHOICES_PER_QUESTION = 4


class Command(BaseCommand):
    help = "fixtures/questions/<slug>.json dosyasından kategori ve soruları yükler (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Dosya bulunamadı: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        category_data = data["category"]
        questions_data = data["questions"]

        self._validate(questions_data)

        with transaction.atomic():
            category, _ = Category.objects.update_or_create(
                slug=category_data["slug"],
                defaults={
                    "name": category_data["name"],
                    "icon": category_data["icon"],
                    "color": category_data["color"],
                    "order": category_data.get("order", 0),
                },
            )

            created_count = 0
            updated_count = 0

            for question_data in questions_data:
                question, created = Question.objects.update_or_create(
                    category=category,
                    text=question_data["text"],
                    defaults={"difficulty": question_data["difficulty"], "is_active": True},
                )
                question.choices.all().delete()
                Choice.objects.bulk_create(
                    [
                        Choice(
                            question=question,
                            text=choice_text,
                            is_correct=(index == question_data["answer"]),
                        )
                        for index, choice_text in enumerate(question_data["choices"])
                    ]
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            summary = f"{category.name}: {created_count} yeni, {updated_count} güncellendi."
            if options["dry_run"]:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING(f"[dry-run] {summary} (kaydedilmedi)"))
            else:
                self.stdout.write(self.style.SUCCESS(summary))

    def _validate(self, questions_data):
        for question_data in questions_data:
            text = question_data["text"]
            if len(text) > MAX_QUESTION_TEXT_LENGTH:
                raise CommandError(f"Soru {MAX_QUESTION_TEXT_LENGTH} karakterden uzun: {text!r}")

            choices = question_data["choices"]
            if len(choices) != CHOICES_PER_QUESTION:
                raise CommandError(f"Her soruda tam {CHOICES_PER_QUESTION} şık olmalı: {text!r}")

            for choice_text in choices:
                if len(choice_text) > MAX_CHOICE_TEXT_LENGTH:
                    raise CommandError(f"Şık {MAX_CHOICE_TEXT_LENGTH} karakterden uzun: {choice_text!r}")

            answer = question_data["answer"]
            if not (0 <= answer < CHOICES_PER_QUESTION):
                raise CommandError(f"Geçersiz answer indeksi: {answer!r}")
