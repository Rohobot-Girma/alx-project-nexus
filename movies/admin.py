from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Movie, Genre, UserFavorite, MovieRating


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    """
    Movie admin interface.
    """
    list_display = [
        'title', 'release_year', 'vote_average', 'popularity', 
        'vote_count', 'poster_thumbnail', 'created_at'
    ]
    list_filter = [
        'adult', 'original_language', 'release_date',
        'created_at', 'updated_at'
    ]
    search_fields = ['title', 'original_title', 'overview']
    ordering = ['-popularity', '-vote_average']
    readonly_fields = ['tmdb_id', 'created_at', 'updated_at', 'poster_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tmdb_id', 'title', 'original_title', 'overview')
        }),
        ('Release & Classification', {
            'fields': ('release_date', 'adult', 'original_language')
        }),
        ('Images', {
            'fields': ('poster_path', 'backdrop_path', 'poster_preview')
        }),
        ('Statistics', {
            'fields': ('popularity', 'vote_average', 'vote_count')
        }),
        ('Metadata', {
            'fields': ('genre_ids', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def release_year(self, obj):
        """Display release year."""
        return obj.release_year
    release_year.short_description = 'Year'
    release_year.admin_order_field = 'release_date'
    
    def poster_thumbnail(self, obj):
        """Display poster thumbnail in list view."""
        if obj.poster_path:
            return format_html(
                '<img src="{}" width="50" height="75" style="object-fit: cover;" />',
                obj.poster_path
            )
        return "No Poster"
    poster_thumbnail.short_description = 'Poster'
    
    def poster_preview(self, obj):
        """Display poster preview in detail view."""
        if obj.poster_path:
            return format_html(
                '<img src="{}" width="200" height="300" style="object-fit: cover;" />',
                obj.poster_path
            )
        return "No Poster Available"
    poster_preview.short_description = 'Poster Preview'


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    """
    Genre admin interface.
    """
    list_display = ['name', 'tmdb_id', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    """
    UserFavorite admin interface.
    """
    list_display = ['user', 'movie', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'movie__title']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'movie')


@admin.register(MovieRating)
class MovieRatingAdmin(admin.ModelAdmin):
    """
    MovieRating admin interface.
    """
    list_display = ['user', 'movie', 'rating', 'review_preview', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__email', 'movie__title', 'review']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('user', 'movie', 'rating', 'review')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def review_preview(self, obj):
        """Display review preview."""
        if obj.review:
            return obj.review[:50] + "..." if len(obj.review) > 50 else obj.review
        return "No Review"
    review_preview.short_description = 'Review Preview'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'movie')