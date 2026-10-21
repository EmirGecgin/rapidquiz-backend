from rest_framework import serializers

from .models import QuizSession


class StartSessionRequestSerializer(serializers.Serializer):
    category = serializers.SlugField()
    platform = serializers.ChoiceField(choices=QuizSession.Platform.choices)


class AnswerRequestSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField(allow_null=True)


class FinishRequestSerializer(serializers.Serializer):
    player_name = serializers.CharField(allow_blank=True, max_length=100)
