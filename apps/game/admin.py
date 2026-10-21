from django.contrib import admin

from .models import QuizSession


@admin.action(description="Seçili turları gizle")
def hide_sessions(modeladmin, request, queryset):
    queryset.update(is_hidden=True)


@admin.action(description="Seçili turların gizliliğini kaldır")
def unhide_sessions(modeladmin, request, queryset):
    queryset.update(is_hidden=False)


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "player_name", "score", "status", "is_hidden", "created_at", "finished_at")
    list_filter = ("category", "status", "is_hidden", "platform")
    search_fields = ("player_name", "id")
    actions = [hide_sessions, unhide_sessions]
