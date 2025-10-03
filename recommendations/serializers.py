from rest_framework import serializers
from .models import Recommendation, RecommendationCache, UserInteraction
from movies.serializers import MovieListSerializer


class RecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for Recommendation model.
    """
    movie = MovieListSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'movie', 'recommendation_type', 'score', 'reason',
            'metadata', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserInteractionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserInteraction model.
    """
    movie = MovieListSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserInteraction
        fields = [
            'id', 'user', 'movie', 'interaction_type', 'value',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class RecommendationCacheSerializer(serializers.ModelSerializer):
    """
    Serializer for RecommendationCache model.
    """
    class Meta:
        model = RecommendationCache
        fields = [
            'id', 'cache_key', 'cache_type', 'data', 'user',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']
