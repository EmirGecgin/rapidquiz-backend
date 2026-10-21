from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Category, Choice, Question


class ChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(active_forms) != 4:
            raise ValidationError("Her soruda tam 4 şık olmalı.")

        correct_count = sum(1 for form in active_forms if form.cleaned_data.get("is_correct"))
        if correct_count != 1:
            raise ValidationError("Her soruda tam 1 doğru şık olmalı.")


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
    extra = 4
    min_num = 4
    max_num = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "category", "difficulty", "is_active")
    list_filter = ("category", "difficulty", "is_active")
    search_fields = ("text",)
    inlines = [ChoiceInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    ordering = ("order",)
    prepopulated_fields = {"slug": ("name",)}
