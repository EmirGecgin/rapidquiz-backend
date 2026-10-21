from django.conf import settings
from django.contrib import admin
from django.urls import path

from .views import health_check

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
]
