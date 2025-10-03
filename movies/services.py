import requests
import logging
from typing import List, Dict, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Movie, Genre

logger = logging.getLogger(__name__)


class TMDBService:
    """
    Service class for interacting with TMDb API.
    Handles movie data fetching, caching, and error management.
    """
    
    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_IMAGE_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Make a request to TMDb API with error handling.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            Response data or None if error
        """
        if not self.api_key:
            logger.error("TMDb API key not configured")
            return None
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TMDb API request: {e}")
            return None
    
    def get_trending_movies(self, page: int = 1, time_window: str = 'week') -> Optional[Dict]:
        """
        Fetch trending movies from TMDb.
        
        Args:
            page: Page number
            time_window: 'day' or 'week'
            
        Returns:
            Trending movies data
        """
        cache_key = f"trending_movies_{time_window}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached trending movies for {time_window}, page {page}")
            return cached_data
        
        endpoint = f"/trending/movie/{time_window}"
        data = self._make_request(endpoint, {'page': page})
        
        if data:
            # Cache for 1 hour
            cache.set(cache_key, data, 3600)
            logger.info(f"Cached trending movies for {time_window}, page {page}")
        
        return data
    
    def get_popular_movies(self, page: int = 1) -> Optional[Dict]:
        """
        Fetch popular movies from TMDb.
        
        Args:
            page: Page number
            
        Returns:
            Popular movies data
        """
        cache_key = f"popular_movies_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached popular movies for page {page}")
            return cached_data
        
        endpoint = "/movie/popular"
        data = self._make_request(endpoint, {'page': page})
        
        if data:
            # Cache for 2 hours
            cache.set(cache_key, data, 7200)
            logger.info(f"Cached popular movies for page {page}")
        
        return data
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Fetch detailed movie information from TMDb.
        
        Args:
            movie_id: TMDb movie ID
            
        Returns:
            Movie details data
        """
        cache_key = f"movie_details_{movie_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached movie details for ID {movie_id}")
            return cached_data
        
        endpoint = f"/movie/{movie_id}"
        data = self._make_request(endpoint)
        
        if data:
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            logger.info(f"Cached movie details for ID {movie_id}")
        
        return data
    
    def get_similar_movies(self, movie_id: int, page: int = 1) -> Optional[Dict]:
        """
        Fetch similar movies from TMDb.
        
        Args:
            movie_id: TMDb movie ID
            page: Page number
            
        Returns:
            Similar movies data
        """
        cache_key = f"similar_movies_{movie_id}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached similar movies for ID {movie_id}, page {page}")
            return cached_data
        
        endpoint = f"/movie/{movie_id}/similar"
        data = self._make_request(endpoint, {'page': page})
        
        if data:
            # Cache for 12 hours
            cache.set(cache_key, data, 43200)
            logger.info(f"Cached similar movies for ID {movie_id}, page {page}")
        
        return data
    
    def search_movies(self, query: str, page: int = 1) -> Optional[Dict]:
        """
        Search movies on TMDb.
        
        Args:
            query: Search query
            page: Page number
            
        Returns:
            Search results data
        """
        cache_key = f"search_movies_{query}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached search results for '{query}', page {page}")
            return cached_data
        
        endpoint = "/search/movie"
        data = self._make_request(endpoint, {
            'query': query,
            'page': page,
            'include_adult': False
        })
        
        if data:
            # Cache for 1 hour
            cache.set(cache_key, data, 3600)
            logger.info(f"Cached search results for '{query}', page {page}")
        
        return data
    
    def get_genres(self) -> Optional[Dict]:
        """
        Fetch movie genres from TMDb.
        
        Returns:
            Genres data
        """
        cache_key = "movie_genres"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info("Returning cached movie genres")
            return cached_data
        
        endpoint = "/genre/movie/list"
        data = self._make_request(endpoint)
        
        if data:
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            logger.info("Cached movie genres")
        
        return data
    
    def get_movies_by_genre(self, genre_id: int, page: int = 1) -> Optional[Dict]:
        """
        Fetch movies by genre from TMDb.
        
        Args:
            genre_id: TMDb genre ID
            page: Page number
            
        Returns:
            Movies by genre data
        """
        cache_key = f"movies_by_genre_{genre_id}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached movies for genre {genre_id}, page {page}")
            return cached_data
        
        endpoint = "/discover/movie"
        data = self._make_request(endpoint, {
            'with_genres': genre_id,
            'page': page,
            'sort_by': 'popularity.desc',
            'include_adult': False
        })
        
        if data:
            # Cache for 2 hours
            cache.set(cache_key, data, 7200)
            logger.info(f"Cached movies for genre {genre_id}, page {page}")
        
        return data


class MovieDataService:
    """
    Service class for managing movie data in the database.
    """
    
    @staticmethod
    def create_or_update_movie(tmdb_data: Dict) -> Optional[Movie]:
        """
        Create or update a movie in the database from TMDb data.
        
        Args:
            tmdb_data: Movie data from TMDb API
            
        Returns:
            Movie instance or None
        """
        try:
            # Extract release date
            release_date = None
            if tmdb_data.get('release_date'):
                from datetime import datetime
                try:
                    release_date = datetime.strptime(tmdb_data['release_date'], '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Invalid release date format: {tmdb_data['release_date']}")
            
            # Create full image URLs
            poster_path = None
            backdrop_path = None
            
            if tmdb_data.get('poster_path'):
                poster_path = f"{settings.TMDB_IMAGE_BASE_URL}{tmdb_data['poster_path']}"
            
            if tmdb_data.get('backdrop_path'):
                backdrop_path = f"{settings.TMDB_IMAGE_BASE_URL}{tmdb_data['backdrop_path']}"
            
            movie, created = Movie.objects.update_or_create(
                tmdb_id=tmdb_data['id'],
                defaults={
                    'title': tmdb_data.get('title', ''),
                    'original_title': tmdb_data.get('original_title', ''),
                    'overview': tmdb_data.get('overview', ''),
                    'release_date': release_date,
                    'poster_path': poster_path,
                    'backdrop_path': backdrop_path,
                    'adult': tmdb_data.get('adult', False),
                    'original_language': tmdb_data.get('original_language', ''),
                    'popularity': tmdb_data.get('popularity', 0.0),
                    'vote_average': tmdb_data.get('vote_average', 0.0),
                    'vote_count': tmdb_data.get('vote_count', 0),
                    'genre_ids': tmdb_data.get('genre_ids', []),
                }
            )
            
            action = "Created" if created else "Updated"
            logger.info(f"{action} movie: {movie.title} (TMDb ID: {movie.tmdb_id})")
            return movie
            
        except Exception as e:
            logger.error(f"Error creating/updating movie: {e}")
            return None
    
    @staticmethod
    def sync_genres():
        """
        Sync genres from TMDb to the database.
        
        Returns:
            Number of genres synced
        """
        tmdb_service = TMDBService()
        genres_data = tmdb_service.get_genres()
        
        if not genres_data or 'genres' not in genres_data:
            logger.error("Failed to fetch genres from TMDb")
            return 0
        
        synced_count = 0
        for genre_data in genres_data['genres']:
            try:
                genre, created = Genre.objects.update_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
                if created:
                    synced_count += 1
                    logger.info(f"Created genre: {genre.name}")
            except Exception as e:
                logger.error(f"Error syncing genre {genre_data}: {e}")
        
        logger.info(f"Synced {synced_count} new genres")
        return synced_count
    
    @staticmethod
    def bulk_sync_movies(movies_data: List[Dict]) -> int:
        """
        Bulk sync movies from TMDb data.
        
        Args:
            movies_data: List of movie data from TMDb
            
        Returns:
            Number of movies synced
        """
        synced_count = 0
        for movie_data in movies_data:
            if MovieDataService.create_or_update_movie(movie_data):
                synced_count += 1
        
        logger.info(f"Bulk synced {synced_count} movies")
        return synced_count
