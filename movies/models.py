from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Movie(models.Model):
    """
    Movie model to store movie information from TMDb API.
    """
    tmdb_id = models.IntegerField(unique=True, help_text="TMDb movie ID")
    title = models.CharField(max_length=200)
    original_title = models.CharField(max_length=200, blank=True)
    overview = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    poster_path = models.URLField(blank=True)
    backdrop_path = models.URLField(blank=True)
    adult = models.BooleanField(default=False)
    original_language = models.CharField(max_length=10, blank=True)
    popularity = models.FloatField(default=0.0)
    vote_average = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        default=0.0
    )
    vote_count = models.IntegerField(default=0)
    genre_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'movies'
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'
        ordering = ['-popularity', '-vote_average']
        indexes = [
            models.Index(fields=['popularity']),
            models.Index(fields=['vote_average']),
            models.Index(fields=['release_date']),
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['genre_ids']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.release_date.year if self.release_date else 'N/A'})"
    
    @property
    def full_poster_url(self):
        """Return the full poster URL."""
        if self.poster_path:
            return self.poster_path
        return None
    
    @property
    def full_backdrop_url(self):
        """Return the full backdrop URL."""
        if self.backdrop_path:
            return self.backdrop_path
        return None
    
    @property
    def release_year(self):
        """Return the release year."""
        return self.release_date.year if self.release_date else None


class Genre(models.Model):
    """
    Genre model to store movie genres.
    """
    tmdb_id = models.IntegerField(unique=True, help_text="TMDb genre ID")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'genres'
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserFavorite(models.Model):
    """
    Model to store user's favorite movies.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='favorite_movies'
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_favorites'
        verbose_name = 'User Favorite'
        verbose_name_plural = 'User Favorites'
        unique_together = ['user', 'movie']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.movie.title}"


class MovieRating(models.Model):
    """
    Model to store user ratings for movies.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='movie_ratings'
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='user_ratings'
    )
    rating = models.FloatField(
        validators=[MinValueValidator(0.5), MaxValueValidator(5.0)],
        help_text="Rating from 0.5 to 5.0 stars"
    )
    review = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'movie_ratings'
        verbose_name = 'Movie Rating'
        verbose_name_plural = 'Movie Ratings'
        unique_together = ['user', 'movie']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} rated {self.movie.title}: {self.rating}/5.0"