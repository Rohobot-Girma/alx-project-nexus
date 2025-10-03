from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Recommendation(models.Model):
    """
    Model to store personalized movie recommendations for users.
    """
    RECOMMENDATION_TYPES = [
        ('trending', 'Trending'),
        ('popular', 'Popular'),
        ('similar', 'Similar Movies'),
        ('genre_based', 'Genre Based'),
        ('collaborative', 'Collaborative Filtering'),
        ('content_based', 'Content Based'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendations',
        null=True,
        blank=True,
        help_text="Null for general recommendations (trending, popular)"
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPES,
        help_text="Type of recommendation algorithm used"
    )
    score = models.FloatField(
        default=0.0,
        help_text="Recommendation score/confidence"
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable reason for recommendation"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for the recommendation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this recommendation expires"
    )
    
    class Meta:
        db_table = 'recommendations'
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
        unique_together = ['user', 'movie', 'recommendation_type']
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'recommendation_type']),
            models.Index(fields=['recommendation_type', 'created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'General'
        return f"{user_str} - {self.movie.title} ({self.recommendation_type})"
    
    @property
    def is_expired(self):
        """Check if the recommendation has expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class RecommendationCache(models.Model):
    """
    Model to cache recommendation results for better performance.
    """
    CACHE_TYPES = [
        ('trending', 'Trending Movies'),
        ('popular', 'Popular Movies'),
        ('genre_cache', 'Genre-based Cache'),
        ('user_cache', 'User-specific Cache'),
    ]
    
    cache_key = models.CharField(max_length=200, unique=True)
    cache_type = models.CharField(max_length=20, choices=CACHE_TYPES)
    data = models.JSONField(help_text="Cached recommendation data")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User-specific cache (null for general cache)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'recommendation_cache'
        verbose_name = 'Recommendation Cache'
        verbose_name_plural = 'Recommendation Caches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cache_type', 'expires_at']),
            models.Index(fields=['user', 'cache_type']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'General'
        return f"{user_str} - {self.cache_type} ({self.cache_key[:50]}...)"
    
    @property
    def is_expired(self):
        """Check if the cache has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at


class UserInteraction(models.Model):
    """
    Model to track user interactions with movies for recommendation learning.
    """
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('favorite', 'Favorite'),
        ('rating', 'Rating'),
        ('watchlist', 'Add to Watchlist'),
        ('search', 'Search'),
        ('click', 'Click'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    value = models.FloatField(
        null=True,
        blank=True,
        help_text="Numeric value for rating or other interactions"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional interaction metadata"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_interactions'
        verbose_name = 'User Interaction'
        verbose_name_plural = 'User Interactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['movie', 'interaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} {self.interaction_type} {self.movie.title}"