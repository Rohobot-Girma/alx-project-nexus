from rest_framework import status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Movie, Genre, UserFavorite, MovieRating
from .serializers import (
    MovieSerializer, MovieListSerializer, MovieDetailSerializer,
    UserFavoriteSerializer, MovieRatingSerializer,
    MovieSearchSerializer, MovieFilterSerializer, GenreSerializer
)
from .services import TMDBService, MovieDataService

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for movie lists.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TrendingMoviesView(ListAPIView):
    """
    View to get trending movies from TMDb.
    """
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
        """Get trending movies."""
        time_window = request.query_params.get('time_window', 'week')
        page = int(request.query_params.get('page', 1))
        
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_trending_movies(page=page, time_window=time_window)
        
        if not tmdb_data:
            return Response(
                {'error': 'Failed to fetch trending movies from TMDb'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Sync movies to database
        movies_data = tmdb_data.get('results', [])
        synced_movies = []
        for movie_data in movies_data:
            movie = MovieDataService.create_or_update_movie(movie_data)
            if movie:
                synced_movies.append(movie)
        
        # Serialize and paginate
        serializer = self.get_serializer(synced_movies, many=True)
        
        # Create paginated response
        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(synced_movies, request)
        serializer = self.get_serializer(paginated_data, many=True)
        
        return paginator.get_paginated_response(serializer.data)


# Import additional views
from .views_additional import (
    MovieDetailView, MovieSearchView, MovieListView, GenreListView,
    UserFavoritesView, RemoveFavoriteView, MovieRatingView, user_ratings_view
)


class PopularMoviesView(ListAPIView):
    """
    View to get popular movies from TMDb.
    """
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
        """Get popular movies."""
        page = int(request.query_params.get('page', 1))
        
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_popular_movies(page=page)
        
        if not tmdb_data:
            return Response(
                {'error': 'Failed to fetch popular movies from TMDb'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Sync movies to database
        movies_data = tmdb_data.get('results', [])
        synced_movies = []
        for movie_data in movies_data:
            movie = MovieDataService.create_or_update_movie(movie_data)
            if movie:
                synced_movies.append(movie)
        
        # Serialize and paginate
        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(synced_movies, request)
        serializer = self.get_serializer(paginated_data, many=True)
        
        return paginator.get_paginated_response(serializer.data)