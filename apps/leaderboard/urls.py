from django.urls import path

from .views import LeaderboardView

urlpatterns = [
    path("leaderboard/<slug:slug>/", LeaderboardView.as_view(), name="leaderboard"),
]
