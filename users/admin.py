from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface.
    """
    list_display = [
        'email', 'username', 'first_name', 'last_name', 
        'is_active', 'date_joined', 'preferred_genres_count'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 
        'created_at', 'date_joined'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('date_of_birth', 'bio', 'avatar')
        }),
        ('Movie Preferences', {
            'fields': ('preferred_genres', 'preferred_languages', 'preferred_countries'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def preferred_genres_count(self, obj):
        """Display count of preferred genres."""
        return len(obj.preferred_genres) if obj.preferred_genres else 0
    preferred_genres_count.short_description = 'Preferred Genres Count'
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        return super().get_queryset(request).select_related()