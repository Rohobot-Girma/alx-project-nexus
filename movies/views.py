from rest_framework import status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Movie
from .serializers import MovieListSerializer, MovieDetailSerializer
from .services import TMDBService, MovieDataService

# Import models and serializers from users app
try:
    from users.models import UserFavorite, MovieRating
    from users.serializers import UserFavoriteSerializer, MovieRatingSerializer
except ImportError:
    # If users app doesn't exist yet, define placeholder classes
    UserFavorite = None
    MovieRating = None
    UserFavoriteSerializer = None
    MovieRatingSerializer = None

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for movie lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MovieDetailView(APIView):
    """Get detailed information about a specific movie by TMDB ID."""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get movie details",
        operation_description="Retrieve detailed information about a specific movie from TMDb API",
        manual_parameters=[
            openapi.Parameter(
                'append_to_response',
                openapi.IN_QUERY,
                description="Additional data to include (comma-separated): credits,videos,similar,recommendations",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Movie details",
                schema=MovieDetailSerializer
            ),
            404: openapi.Response(description="Movie not found"),
            500: openapi.Response(description="TMDb API error")
        }
    )
    @method_decorator(cache_page(60 * 60))  # Cache for 1 hour
    def get(self, request, tmdb_id, *args, **kwargs):
        logger.info(f"🎬 Starting movie details request for ID: {tmdb_id}")
        
        # Validate TMDB ID
        if not tmdb_id or not str(tmdb_id).isdigit():
            logger.error(f"❌ Invalid TMDB ID: {tmdb_id}")
            return Response(
                {'error': 'Invalid TMDB ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check cache first
        cache_key = f'movie_detail_{tmdb_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"✅ Returning cached data for movie {tmdb_id}")
            return Response(cached_data)

        # Get additional data to include
        append_to_response = request.query_params.get('append_to_response', 'credits,videos')
        logger.info(f"📋 Request parameters - append_to_response: {append_to_response}")
        
        try:
            logger.info(f"🔧 Initializing TMDBService...")
            tmdb_service = TMDBService()
            logger.info(f"✅ TMDBService initialized")
            
            logger.info(f"🌐 Calling TMDB API for movie ID: {tmdb_id}")
            movie_data = tmdb_service.get_movie_details(
                movie_id=tmdb_id,
                append_to_response=append_to_response
            )

            logger.info(f"📊 TMDB API response: {movie_data is not None}")
            
            if not movie_data:
                logger.error(f"❌ TMDB service returned None for movie {tmdb_id}")
                return Response(
                    {'error': 'Movie not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if it's an error response from TMDB
            if 'success' in movie_data and not movie_data['success']:
                logger.error(f"❌ TMDB API error: {movie_data.get('status_message')}")
                return Response(
                    {'error': movie_data.get('status_message', 'Movie not found')}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if movie data has id (means it's valid)
            if 'id' not in movie_data:
                logger.error(f"❌ Movie data missing ID field")
                return Response(
                    {'error': 'Movie not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            logger.info(f"✅ TMDB data valid, title: {movie_data.get('title')}")
            logger.info(f"🔧 Calling MovieDataService.create_or_update_movie...")
            
            # Sync movie to our database
            movie = MovieDataService.create_or_update_movie(movie_data)
            
            logger.info(f"📝 MovieDataService returned: {movie}")
            
            if not movie:
                logger.error(f"❌ MovieDataService returned None - database sync failed")
                return Response(
                    {'error': 'Failed to process movie data'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f"✅ Movie synced successfully: {movie.title}")
            logger.info(f"🔧 Creating serializer...")
            
            # Serialize the data
            serializer = MovieDetailSerializer(movie, context={'tmdb_data': movie_data})
            
            logger.info(f"✅ Serializer created successfully")
            
            # Cache the response
            cache.set(cache_key, serializer.data, 3600)  # 1 hour cache
            logger.info(f"💾 Response cached for movie {tmdb_id}")
            
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Error in MovieDetailView for ID {tmdb_id}: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to fetch movie details: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class MovieSearchView(ListAPIView):
    """Search for movies by title."""
    serializer_class = MovieListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        operation_summary="Search movies",
        operation_description="Search for movies by title using TMDb API",
        manual_parameters=[
            openapi.Parameter(
                'query',
                openapi.IN_QUERY,
                description="Search query",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="Filter by year",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="List of search results",
                schema=MovieListSerializer(many=True)
            ),
            400: openapi.Response(description="Missing search query"),
            500: openapi.Response(description="TMDb API error")
        }
    )
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '').strip()
        
        if not query:
            return Response(
                {'error': 'Search query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        page = int(request.query_params.get('page', 1))
        year = request.query_params.get('year')

        try:
            tmdb_service = TMDBService()
            search_data = tmdb_service.search_movies(
                query=query, 
                page=page, 
                year=year
            )

            if not search_data:
                return Response(
                    {'error': 'Failed to search movies'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            movies_data = search_data.get('results', [])
            synced_movies = []
            for movie_data in movies_data:
                movie = MovieDataService.create_or_update_movie(movie_data)
                if movie:
                    synced_movies.append(movie)

            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(synced_movies, request)
            serializer = self.get_serializer(paginated_data, many=True)

            response = paginator.get_paginated_response(serializer.data)
            # Add search metadata
            response.data['search_query'] = query
            response.data['total_results'] = search_data.get('total_results', 0)
            
            return response

        except Exception as e:
            logger.error(f"Error searching movies: {str(e)}")
            return Response(
                {'error': 'Search failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrendingMoviesView(ListAPIView):
    """Get trending movies from TMDb."""
    serializer_class = MovieListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        operation_summary="Get trending movies",
        operation_description="Retrieve trending movies from TMDb API",
        manual_parameters=[
            openapi.Parameter(
                'time_window',
                openapi.IN_QUERY,
                description="Time window for trending (day or week)",
                type=openapi.TYPE_STRING,
                enum=['day', 'week'],
                default='week'
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1
            )
        ],
        responses={
            200: openapi.Response(
                description="List of trending movies",
                schema=MovieListSerializer(many=True)
            ),
            500: openapi.Response(description="TMDb API error")
        }
    )
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request, *args, **kwargs):
        time_window = request.query_params.get('time_window', 'week')
        page = int(request.query_params.get('page', 1))

        try:
            tmdb_service = TMDBService()
            tmdb_data = tmdb_service.get_trending_movies(page=page, time_window=time_window)

            if not tmdb_data:
                return Response(
                    {'error': 'Failed to fetch trending movies from TMDb'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            movies_data = tmdb_data.get('results', [])
            synced_movies = []
            for movie_data in movies_data:
                movie = MovieDataService.create_or_update_movie(movie_data)
                if movie:
                    synced_movies.append(movie)

            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(synced_movies, request)
            serializer = self.get_serializer(paginated_data, many=True)

            return paginator.get_paginated_response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error fetching trending movies: {str(e)}")
            return Response(
                {'error': 'Failed to fetch trending movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PopularMoviesView(ListAPIView):
    """Get popular movies from TMDb."""
    serializer_class = MovieListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        operation_summary="Get popular movies",
        operation_description="Retrieve popular movies from TMDb API",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number",
                type=openapi.TYPE_INTEGER,
                default=1
            )
        ],
        responses={
            200: openapi.Response(
                description="List of popular movies",
                schema=MovieListSerializer(many=True)
            ),
            500: openapi.Response(description="TMDb API error")
        }
    )
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request, *args, **kwargs):
        page = int(request.query_params.get('page', 1))

        try:
            tmdb_service = TMDBService()
            tmdb_data = tmdb_service.get_popular_movies(page=page)

            if not tmdb_data:
                return Response(
                    {'error': 'Failed to fetch popular movies from TMDb'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            movies_data = tmdb_data.get('results', [])
            synced_movies = []
            for movie_data in movies_data:
                movie = MovieDataService.create_or_update_movie(movie_data)
                if movie:
                    synced_movies.append(movie)

            paginator = self.pagination_class()
            paginated_data = paginator.paginate_queryset(synced_movies, request)
            serializer = self.get_serializer(paginated_data, many=True)

            return paginator.get_paginated_response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error fetching popular movies: {str(e)}")
            return Response(
                {'error': 'Failed to fetch popular movies'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenreListView(APIView):
    """Get list of available movie genres."""
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Get movie genres",
        operation_description="Retrieve list of available movie genres from TMDb",
        responses={
            200: openapi.Response(description="List of genres"),
            500: openapi.Response(description="TMDb API error")
        }
    )
    @method_decorator(cache_page(60 * 60 * 24))  # Cache for 24 hours (genres don't change often)
    def get(self, request, *args, **kwargs):
        try:
            tmdb_service = TMDBService()
            genres = tmdb_service.get_movie_genres()
            
            if not genres:
                return Response(
                    {'error': 'Failed to fetch genres'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(genres)
            
        except Exception as e:
            logger.error(f"Error fetching genres: {str(e)}")
            return Response(
                {'error': 'Failed to fetch genres'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MovieListView(ListAPIView):
    """Get all movies from local database with filtering and pagination."""
    serializer_class = MovieListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genre_ids', 'release_date', 'vote_average', 'adult']
    search_fields = ['title', 'original_title', 'overview']
    ordering_fields = ['popularity', 'vote_average', 'release_date', 'title']
    ordering = ['-popularity']

    @swagger_auto_schema(
        operation_summary="List movies with filtering",
        operation_description="Get paginated list of movies with filtering, search, and sorting options",
        manual_parameters=[
            openapi.Parameter(
                'genre_ids',
                openapi.IN_QUERY,
                description="Filter by genre IDs (comma-separated)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search in title, original_title, or overview",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Order by field (prefix with - for descending)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserFavoritesView(APIView):
    """Manage user's favorite movies."""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get user favorites",
        operation_description="Retrieve list of user's favorite movies",
        responses={
            200: openapi.Response(description="User favorites list"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        """Get user's favorite movies."""
        if UserFavorite is None:
            return Response(
                {'error': 'User favorites feature not available'}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        favorites = UserFavorite.objects.filter(user=request.user).select_related('movie')
        serializer = UserFavoriteSerializer(favorites, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Add movie to favorites",
        operation_description="Add a movie to user's favorites",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'movie_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Movie ID')
            }
        ),
        responses={
            201: openapi.Response(description="Favorite added"),
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Authentication required"),
            501: openapi.Response(description="Feature not implemented")
        }
    )
    def post(self, request):
        """Add a movie to favorites."""
        if UserFavoriteSerializer is None:
            return Response(
                {'error': 'User favorites feature not available'}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        serializer = UserFavoriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            favorite = serializer.save()
            return Response(UserFavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveFavoriteView(APIView):
    """Remove a movie from user's favorites."""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Remove favorite",
        operation_description="Remove a movie from user's favorites",
        responses={
            204: openapi.Response(description="Successfully removed"),
            404: openapi.Response(description="Favorite not found"),
            401: openapi.Response(description="Authentication required"),
            501: openapi.Response(description="Feature not implemented")
        }
    )
    def delete(self, request, pk):
        """Remove a movie from favorites."""
        if UserFavorite is None:
            return Response(
                {'error': 'User favorites feature not available'}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        try:
            favorite = UserFavorite.objects.get(id=pk, user=request.user)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserFavorite.DoesNotExist:
            return Response(
                {'error': 'Favorite not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MovieRatingView(APIView):
    """Rate and review movies."""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Rate a movie",
        operation_description="Rate and optionally review a movie",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'movie_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Movie ID'),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description='Rating from 0.5 to 5.0'),
                'review': openapi.Schema(type=openapi.TYPE_STRING, description='Optional review text')
            }
        ),
        responses={
            201: openapi.Response(description="Rating created"),
            200: openapi.Response(description="Rating updated"),
            400: openapi.Response(description="Bad request"),
            401: openapi.Response(description="Authentication required"),
            501: openapi.Response(description="Feature not implemented")
        }
    )
    def post(self, request):
        """Rate a movie."""
        if MovieRatingSerializer is None:
            return Response(
                {'error': 'Movie rating feature not available'}, 
                status=status.HTTP_501_NOT_IMPLEMENTED
            )
        
        serializer = MovieRatingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            rating = serializer.save()
            status_code = status.HTTP_201_CREATED if rating.created else status.HTTP_200_OK
            return Response(MovieRatingSerializer(rating).data, status=status_code)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@swagger_auto_schema(
    operation_summary="Get user ratings",
    operation_description="Retrieve all ratings and reviews by the current user",
    responses={
        200: openapi.Response(description="User ratings list"),
        401: openapi.Response(description="Authentication required"),
        501: openapi.Response(description="Feature not implemented")
    }
)
def user_ratings_view(request):
    """Get user's movie ratings."""
    if MovieRating is None:
        return Response(
            {'error': 'Movie ratings feature not available'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    ratings = MovieRating.objects.filter(user=request.user).select_related('movie')
    serializer = MovieRatingSerializer(ratings, many=True)
    return Response(serializer.data)