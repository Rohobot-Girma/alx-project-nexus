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
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, retries: int = 3) -> Optional[Dict]:
        """
        Make a request to TMDb API with error handling and retry logic.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            retries: Number of retry attempts
            
        Returns:
            Response data or None if error
        """
        if not self.api_key:
            logger.error("TMDb API key not configured")
            return None
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    if attempt < retries - 1:
                        import time
                        time.sleep(retry_after)
                        continue
                
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors in response
                if 'success' in data and not data['success']:
                    logger.error(f"TMDb API error: {data.get('status_message', 'Unknown error')}")
                    return None
                
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"TMDb API timeout on attempt {attempt + 1}")
                if attempt == retries - 1:
                    logger.error("TMDb API request timed out after all retries")
                    return None
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"TMDb API connection error on attempt {attempt + 1}")
                if attempt == retries - 1:
                    logger.error("TMDb API connection failed after all retries")
                    return None
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [500, 502, 503, 504]:
                    logger.warning(f"TMDb API server error on attempt {attempt + 1}: {e}")
                    if attempt == retries - 1:
                        logger.error("TMDb API server errors after all retries")
                        return None
                else:
                    logger.error(f"TMDb API HTTP error: {e}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"TMDb API request failed: {e}")
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error in TMDb API request: {e}")
                return None
        
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
    
    def get_movie_details(self, movie_id: int, append_to_response: str = 'credits,videos') -> Optional[Dict]:
        """
        Fetch detailed movie information from TMDb.
        
        Args:
            movie_id: TMDb movie ID
            append_to_response: Additional data to include (comma-separated)
            
        Returns:
            Movie details data
        """
        cache_key = f"movie_details_{movie_id}_{append_to_response.replace(',', '_')}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"✅ Returning cached movie details for ID {movie_id}")
            return cached_data
        
        endpoint = f"/movie/{movie_id}"
        params = {
            'append_to_response': append_to_response,
            'language': 'en-US'
        }
        
        logger.info(f"🎬 Fetching movie details for ID: {movie_id}")
        logger.info(f"📋 Append to response: {append_to_response}")
        
        data = self._make_request(endpoint, params)
        
        if data:
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            logger.info(f"💾 Cached movie details for ID: {movie_id}")
            logger.info(f"✅ Successfully fetched: {data.get('title', 'Unknown')}")
        else:
            logger.error(f"❌ Failed to fetch movie details for ID: {movie_id}")
        
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
            logger.info(f"🎯 Starting create_or_update_movie for TMDB ID: {tmdb_data.get('id')}")
            
            # Extract basic movie info
            tmdb_id = tmdb_data.get('id')
            if not tmdb_id:
                logger.error("❌ No TMDB ID in movie data")
                return None
            
            # Extract release date
            release_date = None
            if tmdb_data.get('release_date'):
                from datetime import datetime
                try:
                    release_date = datetime.strptime(tmdb_data['release_date'], '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Invalid release date format: {tmdb_data['release_date']}")
            
            # Since your model uses URLField, we need to create full URLs
            poster_path = None
            backdrop_path = None
            
            if tmdb_data.get('poster_path'):
                poster_path = f"https://image.tmdb.org/t/p/w500{tmdb_data['poster_path']}"
            
            if tmdb_data.get('backdrop_path'):
                backdrop_path = f"https://image.tmdb.org/t/p/w1280{tmdb_data['backdrop_path']}"
            
            # Extract genre_ids
            genre_ids = []
            if 'genres' in tmdb_data:
                genre_ids = [genre['id'] for genre in tmdb_data['genres']]
            elif 'genre_ids' in tmdb_data:
                genre_ids = tmdb_data['genre_ids']
            
            logger.info(f"📝 Processing movie: {tmdb_data.get('title')}")
            logger.info(f"📅 Release date: {release_date}")
            logger.info(f"🖼️ Poster path: {poster_path}")
            logger.info(f"🎭 Genre IDs: {genre_ids}")
            
            # Create or update the movie
            movie, created = Movie.objects.update_or_create(
                tmdb_id=tmdb_id,
                defaults={
                    'title': tmdb_data.get('title', ''),
                    'original_title': tmdb_data.get('original_title', ''),
                    'overview': tmdb_data.get('overview', ''),
                    'release_date': release_date,
                    'poster_path': poster_path,  # Full URL for URLField
                    'backdrop_path': backdrop_path,  # Full URL for URLField
                    'adult': tmdb_data.get('adult', False),
                    'original_language': tmdb_data.get('original_language', ''),
                    'popularity': tmdb_data.get('popularity', 0.0),
                    'vote_average': tmdb_data.get('vote_average', 0.0),
                    'vote_count': tmdb_data.get('vote_count', 0),
                    'genre_ids': genre_ids,  # JSON field with genre IDs
                }
            )
            
            # Also sync to Genre model if you want ManyToMany relationship
            if 'genres' in tmdb_data:
                MovieDataService._sync_movie_genres(movie, tmdb_data['genres'])
            
            action = "Created" if created else "Updated"
            logger.info(f"✅ {action} movie: {movie.title} (TMDb ID: {movie.tmdb_id})")
            return movie
            
        except Exception as e:
            logger.error(f"❌ Error creating/updating movie: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    @staticmethod
    def _sync_movie_genres(movie: Movie, genres_data: List[Dict]):
        """
        Sync genres for a movie to the Genre model (ManyToMany).
        
        Args:
            movie: Movie instance
            genres_data: List of genre data from TMDb
        """
        try:
            from .models import Genre
            
            genre_instances = []
            for genre_data in genres_data:
                genre, created = Genre.objects.get_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
                genre_instances.append(genre)
            
            # Add genres to movie (ManyToMany)
            movie.genres.add(*genre_instances)
            logger.info(f"✅ Synced {len(genre_instances)} genres for movie: {movie.title}")
            
        except Exception as e:
            logger.error(f"❌ Error syncing genres for movie {movie.title}: {e}")
    
    @staticmethod
    def sync_genres():
        """
        Sync genres from TMDb to the database.
        
        Returns:
            Number of genres synced
        """
        tmdb_service = TMDBService()
        genres_data = tmdb_service.get_movie_genres()
        
        if not genres_data:
            logger.error("❌ Failed to fetch genres from TMDb")
            return 0
        
        synced_count = 0
        for genre_data in genres_data:
            try:
                genre, created = Genre.objects.update_or_create(
                    tmdb_id=genre_data['id'],
                    defaults={'name': genre_data['name']}
                )
                if created:
                    synced_count += 1
                    logger.info(f"✅ Created genre: {genre.name}")
            except Exception as e:
                logger.error(f"❌ Error syncing genre {genre_data}: {e}")
        
        logger.info(f"✅ Synced {synced_count} new genres")
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
        
        logger.info(f"✅ Bulk synced {synced_count} movies")
        return synced_count