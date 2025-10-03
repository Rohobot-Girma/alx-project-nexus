from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Movie, Genre, UserFavorite, MovieRating

User = get_user_model()


class GenreSerializer(serializers.ModelSerializer):
    """
    Serializer for Genre model.
    """
    class Meta:
        model = Genre
        fields = ['id', 'tmdb_id', 'name']


class MovieSerializer(serializers.ModelSerializer):
    """
    Serializer for Movie model.
    """
    genres = GenreSerializer(source='genre_ids', many=True, read_only=True)
    release_year = serializers.ReadOnlyField()
    full_poster_url = serializers.ReadOnlyField()
    full_backdrop_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'title', 'original_title', 'overview',
            'release_date', 'release_year', 'poster_path', 'backdrop_path',
            'full_poster_url', 'full_backdrop_url', 'adult', 'original_language',
            'popularity', 'vote_average', 'vote_count', 'genre_ids', 'genres',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MovieListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for movie lists.
    """
    release_year = serializers.ReadOnlyField()
    full_poster_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'title', 'original_title', 'overview',
            'release_date', 'release_year', 'poster_path', 'full_poster_url',
            'vote_average', 'vote_count', 'genre_ids'
        ]


class MovieDetailSerializer(MovieSerializer):
    """
    Detailed serializer for movie information.
    """
    is_favorite = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    class Meta(MovieSerializer.Meta):
        fields = MovieSerializer.Meta.fields + ['is_favorite', 'user_rating']
    
    def get_is_favorite(self, obj):
        """Check if movie is in user's favorites."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserFavorite.objects.filter(
                user=request.user,
                movie=obj
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get user's rating for the movie."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = MovieRating.objects.get(user=request.user, movie=obj)
                return {
                    'rating': rating.rating,
                    'review': rating.review,
                    'created_at': rating.created_at
                }
            except MovieRating.DoesNotExist:
                return None
        return None


class UserFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for UserFavorite model.
    """
    movie = MovieListSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserFavorite
        fields = ['id', 'movie', 'movie_id', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Create a new favorite."""
        user = self.context['request'].user
        movie_id = validated_data.pop('movie_id')
        
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            raise serializers.ValidationError("Movie not found.")
        
        favorite, created = UserFavorite.objects.get_or_create(
            user=user,
            movie=movie
        )
        
        if not created:
            raise serializers.ValidationError("Movie is already in favorites.")
        
        return favorite


class MovieRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for MovieRating model.
    """
    movie = MovieListSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = MovieRating
        fields = [
            'id', 'movie', 'movie_id', 'user', 'rating', 'review',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating value."""
        if not (0.5 <= value <= 5.0):
            raise serializers.ValidationError("Rating must be between 0.5 and 5.0.")
        return value
    
    def create(self, validated_data):
        """Create or update a movie rating."""
        user = self.context['request'].user
        movie_id = validated_data.pop('movie_id')
        
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            raise serializers.ValidationError("Movie not found.")
        
        rating, created = MovieRating.objects.update_or_create(
            user=user,
            movie=movie,
            defaults=validated_data
        )
        
        return rating


class MovieSearchSerializer(serializers.Serializer):
    """
    Serializer for movie search parameters.
    """
    query = serializers.CharField(max_length=200, help_text="Search query")
    page = serializers.IntegerField(min_value=1, max_value=1000, default=1)
    include_adult = serializers.BooleanField(default=False)
    
    def validate_query(self, value):
        """Validate search query."""
        if not value.strip():
            raise serializers.ValidationError("Search query cannot be empty.")
        return value.strip()


class MovieFilterSerializer(serializers.Serializer):
    """
    Serializer for movie filtering parameters.
    """
    genre = serializers.CharField(required=False, help_text="Genre name or ID")
    year = serializers.IntegerField(required=False, min_value=1900, max_value=2030)
    language = serializers.CharField(required=False, max_length=10)
    min_rating = serializers.FloatField(required=False, min_value=0.0, max_value=10.0)
    max_rating = serializers.FloatField(required=False, min_value=0.0, max_value=10.0)
    sort_by = serializers.ChoiceField(
        choices=[
            ('popularity.desc', 'Popularity (Descending)'),
            ('popularity.asc', 'Popularity (Ascending)'),
            ('vote_average.desc', 'Rating (Descending)'),
            ('vote_average.asc', 'Rating (Ascending)'),
            ('release_date.desc', 'Release Date (Newest)'),
            ('release_date.asc', 'Release Date (Oldest)'),
            ('title.asc', 'Title (A-Z)'),
            ('title.desc', 'Title (Z-A)'),
        ],
        default='popularity.desc'
    )
    page = serializers.IntegerField(min_value=1, max_value=1000, default=1)
    
    def validate(self, attrs):
        """Validate filter parameters."""
        min_rating = attrs.get('min_rating')
        max_rating = attrs.get('max_rating')
        
        if min_rating and max_rating and min_rating > max_rating:
            raise serializers.ValidationError(
                "Minimum rating cannot be greater than maximum rating."
            )
        
        return attrs
