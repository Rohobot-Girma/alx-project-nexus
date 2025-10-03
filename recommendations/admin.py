from django.contrib import admin
from django.utils.html import format_html
from .models import Recommendation, RecommendationCache, UserInteraction


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """
    Recommendation admin interface.
    """
    list_display = [
        'user', 'movie', 'recommendation_type', 'score', 
        'reason_preview', 'is_expired', 'created_at'
    ]
    list_filter = [
        'recommendation_type', 'created_at', 'expires_at'
    ]
    search_fields = ['user__email', 'movie__title', 'reason']
    ordering = ['-score', '-created_at']
    
    fieldsets = (
        ('Recommendation Details', {
            'fields': ('user', 'movie', 'recommendation_type', 'score', 'reason')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def reason_preview(self, obj):
        """Display reason preview."""
        if obj.reason:
            return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
        return "No Reason"
    reason_preview.short_description = 'Reason Preview'
    
    def is_expired(self, obj):
        """Display expiration status."""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'movie')


@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    """
    RecommendationCache admin interface.
    """
    list_display = [
        'cache_key_preview', 'cache_type', 'user', 
        'is_expired', 'created_at', 'expires_at'
    ]
    list_filter = ['cache_type', 'created_at', 'expires_at']
    search_fields = ['cache_key', 'user__email']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Cache Information', {
            'fields': ('cache_key', 'cache_type', 'user')
        }),
        ('Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def cache_key_preview(self, obj):
        """Display cache key preview."""
        return obj.cache_key[:50] + "..." if len(obj.cache_key) > 50 else obj.cache_key
    cache_key_preview.short_description = 'Cache Key'
    
    def is_expired(self, obj):
        """Display expiration status."""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    is_expired.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user')


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    """
    UserInteraction admin interface.
    """
    list_display = [
        'user', 'movie', 'interaction_type', 'value', 'created_at'
    ]
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['user__email', 'movie__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Interaction Details', {
            'fields': ('user', 'movie', 'interaction_type', 'value')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'movie')