from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    player_name = serializers.CharField()
    score = serializers.IntegerField()
    correct_count = serializers.IntegerField()
    finished_at = serializers.DateTimeField()
