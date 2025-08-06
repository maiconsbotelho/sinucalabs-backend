from rest_framework import serializers
from .models import Achievement, UserAchievement
from accounts.serializers import UserProfileSerializer


class AchievementSerializer(serializers.ModelSerializer):
    total_unlocked = serializers.ReadOnlyField()
    
    class Meta:
        model = Achievement
        fields = (
            'id', 'code', 'name', 'description', 'icon_url', 
            'category', 'points', 'total_unlocked', 'created_at'
        )


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    user = UserProfileSerializer(read_only=True)
    match_id = serializers.UUIDField(source='match.id', read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = (
            'id', 'achievement', 'user', 'unlocked_at', 'match_id'
        )


class UserAchievementListSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = (
            'id', 'achievement', 'unlocked_at'
        )


class AchievementStatsSerializer(serializers.Serializer):
    total_achievements = serializers.IntegerField()
    unlocked_achievements = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    recent_achievements = UserAchievementListSerializer(many=True)
    achievements_by_category = serializers.DictField()