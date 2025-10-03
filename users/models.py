from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Includes additional fields for user preferences and profile information.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User preferences for movie recommendations
    preferred_genres = models.JSONField(default=list, blank=True)
    preferred_languages = models.JSONField(default=list, blank=True)
    preferred_countries = models.JSONField(default=list, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_preferred_genres_display(self):
        """Return a readable list of preferred genres."""
        return ', '.join(self.preferred_genres) if self.preferred_genres else 'None'
    
    def get_preferred_languages_display(self):
        """Return a readable list of preferred languages."""
        return ', '.join(self.preferred_languages) if self.preferred_languages else 'None'