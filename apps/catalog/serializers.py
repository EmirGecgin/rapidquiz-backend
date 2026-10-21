from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["name", "slug", "icon", "color", "question_count"]
