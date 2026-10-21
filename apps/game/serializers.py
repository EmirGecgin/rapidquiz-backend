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


class SessionCreateResponseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    token = serializers.CharField()
    total_questions = serializers.IntegerField()
    time_limit_ms = serializers.IntegerField()


class ChoiceResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()


class NextQuestionResponseSerializer(serializers.Serializer):
    done = serializers.BooleanField(required=False)
    index = serializers.IntegerField(required=False)
    question_id = serializers.IntegerField(required=False)
    text = serializers.CharField(required=False)
    choices = ChoiceResponseSerializer(many=True, required=False)
    time_limit_ms = serializers.IntegerField(required=False)


class AnswerResponseSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField()
    correct_choice_id = serializers.IntegerField()
    points = serializers.IntegerField()
    score = serializers.IntegerField()
    elapsed_ms = serializers.IntegerField()


class FinishResponseSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    rank = serializers.IntegerField()
    correct_count = serializers.IntegerField()
