from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.game.urls")),
    path("api/v1/", include("apps.leaderboard.urls")),
]
