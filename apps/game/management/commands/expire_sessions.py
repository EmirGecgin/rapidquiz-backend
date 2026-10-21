from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.game.models import QuizSession

EXPIRY_MINUTES = 10


class Command(BaseCommand):
    help = f"{EXPIRY_MINUTES} dakikadan eski aktif oturumları 'expired' olarak işaretler."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=EXPIRY_MINUTES)
        updated = QuizSession.objects.filter(
            status=QuizSession.Status.ACTIVE, created_at__lt=cutoff
        ).update(status=QuizSession.Status.EXPIRED)

        self.stdout.write(self.style.SUCCESS(f"{updated} oturum süresi doldu olarak işaretlendi."))
