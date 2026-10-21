from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import LeaderboardEntrySerializer


class LeaderboardView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter("period", str, description="day | week | all (varsayılan: all)"),
            OpenApiParameter("limit", int, description="1-100 arası, varsayılan 20"),
        ],
        responses=LeaderboardEntrySerializer(many=True),
    )
    def get(self, request, slug):
        period = request.query_params.get("period", "all")
        if period not in services.PERIOD_CHOICES:
            raise ValidationError({"period": "Geçersiz period. day, week veya all olmalı."})

        raw_limit = request.query_params.get("limit", str(services.DEFAULT_LIMIT))
        try:
            limit = int(raw_limit)
        except ValueError:
            raise ValidationError({"limit": "limit bir sayı olmalı."})
        if not (0 < limit <= services.MAX_LIMIT):
            raise ValidationError({"limit": f"limit 1-{services.MAX_LIMIT} arasında olmalı."})

        entries = services.get_leaderboard(slug, period, limit)
        return Response(LeaderboardEntrySerializer(entries, many=True).data)
