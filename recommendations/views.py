from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.cache import cache
import logging

from .models import Recommendation, UserInteraction
from .serializers import RecommendationSerializer, UserInteractionSerializer
from movies.models import Movie, UserFavorite
from movies.services import TMDBService, MovieDataService

logger = logging.getLogger(__name__)


class PersonalizedRecommendationsView(APIView):
    """
    View to get personalized movie recommendations for authenticated users.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get personalized recommendations",
        operation_description="Retrieve personalized movie recommendations based on user preferences and history",
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Number of recommendations to return",
                type=openapi.TYPE_INTEGER,
                default=20
            )
        ],
        responses={
            200: openapi.Response(
                description="List of personalized recommendations",
                schema=RecommendationSerializer(many=True)
            ),
            401: openapi.Response(description="Authentication required")
        }
    )
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def get(self, request):
        """Get personalized recommendations."""
        user = request.user
        limit = int(request.query_params.get('limit', 20))
        
        # Check cache first
        cache_key = f"user_recommendations_{user.id}_{limit}"
        cached_recommendations = cache.get(cache_key)
        
        if cached_recommendations:
            logger.info(f"Returning cached recommendations for user {user.id}")
            return Response(cached_recommendations)
        
        # Generate recommendations based on user preferences
        recommendations = self._generate_recommendations(user, limit)
        
        # Serialize recommendations
        serializer = RecommendationSerializer(recommendations, many=True, context={'request': request})
        response_data = serializer.data
        
        # Cache the results
        cache.set(cache_key, response_data, 600)  # Cache for 10 minutes
        
        return Response(response_data)
    
    def _generate_recommendations(self, user, limit):
        """Generate recommendations based on user preferences."""
        recommendations = []
        
        # Get user's favorite genres
        user_genres = user.preferred_genres or []
        
        # Get user's favorite movies
        user_favorites = UserFavorite.objects.filter(user=user).values_list('movie_id', flat=True)
        
        # Generate genre-based recommendations
        if user_genres:
            genre_recommendations = self._get_genre_based_recommendations(user_genres, limit//2)
            recommendations.extend(genre_recommendations)
        
        # Generate similar recommendations
        if user_favorites:
            similar_recommendations = self._get_similar_recommendations(user_favorites, limit//2)
            recommendations.extend(similar_recommendations)
        
        # Fill with popular movies if needed
        if len(recommendations) < limit:
            popular_recommendations = self._get_popular_recommendations(limit - len(recommendations))
            recommendations.extend(popular_recommendations)
        
        return recommendations[:limit]
    
    def _get_genre_based_recommendations(self, user_genres, limit):
        """Get recommendations based on user's preferred genres."""
        # Convert genre names to IDs (simplified approach)
        genre_mapping = {
            'Action': 28, 'Adventure': 12, 'Animation': 16, 'Comedy': 35,
            'Crime': 80, 'Documentary': 99, 'Drama': 18, 'Family': 10751,
            'Fantasy': 14, 'History': 36, 'Horror': 27, 'Music': 10402,
            'Mystery': 9648, 'Romance': 10749, 'Science Fiction': 878,
            'TV Movie': 10770, 'Thriller': 53, 'War': 10752, 'Western': 37
        }
        
        genre_ids = [genre_mapping.get(genre, None) for genre in user_genres]
        genre_ids = [gid for gid in genre_ids if gid is not None]
        
        if not genre_ids:
            return []
        
        # Get movies with user's preferred genres
        movies = Movie.objects.filter(
            genre_ids__overlap=genre_ids
        ).order_by('-popularity', '-vote_average')[:limit]
        
        # Create recommendation objects
        recommendations = []
        for movie in movies:
            recommendation = Recommendation(
                user=self.request.user,
                movie=movie,
                recommendation_type='genre_based',
                score=0.8,
                reason=f"Recommended based on your preference for {', '.join(user_genres)}"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_similar_recommendations(self, user_favorites, limit):
        """Get recommendations similar to user's favorite movies."""
        # Get movies with similar genres to user's favorites
        favorite_movies = Movie.objects.filter(id__in=user_favorites)
        all_genres = []
        for movie in favorite_movies:
            all_genres.extend(movie.genre_ids)
        
        # Get unique genres
        unique_genres = list(set(all_genres))
        
        if not unique_genres:
            return []
        
        # Get movies with similar genres
        movies = Movie.objects.filter(
            genre_ids__overlap=unique_genres
        ).exclude(id__in=user_favorites).order_by('-popularity')[:limit]
        
        # Create recommendation objects
        recommendations = []
        for movie in movies:
            recommendation = Recommendation(
                user=self.request.user,
                movie=movie,
                recommendation_type='similar',
                score=0.7,
                reason="Recommended based on movies you liked"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_popular_recommendations(self, limit):
        """Get popular movies as recommendations."""
        movies = Movie.objects.filter(
            popularity__gt=10,
            vote_average__gt=6.0
        ).order_by('-popularity')[:limit]
        
        # Create recommendation objects
        recommendations = []
        for movie in movies:
            recommendation = Recommendation(
                user=self.request.user,
                movie=movie,
                recommendation_type='popular',
                score=0.6,
                reason="Popular movies you might enjoy"
            )
            recommendations.append(recommendation)
        
        return recommendations


class TrendingRecommendationsView(APIView):
    """
    View to get trending movie recommendations.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Get trending recommendations",
        operation_description="Retrieve trending movie recommendations",
        manual_parameters=[
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Number of recommendations to return",
                type=openapi.TYPE_INTEGER,
                default=20
            )
        ]
    )
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        """Get trending recommendations."""
        limit = int(request.query_params.get('limit', 20))
        
        # Check cache first
        cache_key = f"trending_recommendations_{limit}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get trending movies from TMDb
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_trending_movies(page=1, time_window='week')
        
        if not tmdb_data:
            return Response(
                {'error': 'Failed to fetch trending movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Sync movies to database
        movies_data = tmdb_data.get('results', [])[:limit]
        synced_movies = []
        for movie_data in movies_data:
            movie = MovieDataService.create_or_update_movie(movie_data)
            if movie:
                synced_movies.append(movie)
        
        # Serialize results
        from movies.serializers import MovieListSerializer
        serializer = MovieListSerializer(synced_movies, many=True)
        
        response_data = {'results': serializer.data}
        
        # Cache the results
        cache.set(cache_key, response_data, 900)  # Cache for 15 minutes
        
        return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@swagger_auto_schema(
    operation_summary="Track user interaction",
    operation_description="Track user interaction with a movie for recommendation learning",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'movie_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'interaction_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['view', 'favorite', 'rating', 'watchlist', 'search', 'click']
            ),
            'value': openapi.Schema(type=openapi.TYPE_NUMBER),
            'metadata': openapi.Schema(type=openapi.TYPE_OBJECT)
        },
        required=['movie_id', 'interaction_type']
    )
)
def track_interaction_view(request):
    """Track user interaction with a movie."""
    movie_id = request.data.get('movie_id')
    interaction_type = request.data.get('interaction_type')
    value = request.data.get('value')
    metadata = request.data.get('metadata', {})
    
    if not movie_id or not interaction_type:
        return Response(
            {'error': 'movie_id and interaction_type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response(
            {'error': 'Movie not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Create interaction
    interaction = UserInteraction.objects.create(
        user=request.user,
        movie=movie,
        interaction_type=interaction_type,
        value=value,
        metadata=metadata
    )
    
    return Response({
        'message': 'Interaction tracked successfully',
        'interaction_id': interaction.id
    }, status=status.HTTP_201_CREATED)