"""
Background tasks for movie data synchronization.
"""

from celery import shared_task
from django.core.cache import cache
from django.conf import settings
import logging

from .services import TMDBService, MovieDataService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_tmdb_data_task(self, categories=None, pages=5):
    """
    Background task to sync TMDb data.
    
    Args:
        categories: List of categories to sync
        pages: Number of pages to fetch per category
    """
    if categories is None:
        categories = ['trending', 'popular']
    
    try:
        logger.info(f"Starting TMDb data sync for categories: {categories}")
        
        tmdb_service = TMDBService()
        total_movies = 0
        
        for category in categories:
            category_movies = 0
            
            for page in range(1, pages + 1):
                try:
                    if category == 'trending':
                        data = tmdb_service.get_trending_movies(page=page, time_window='week')
                    elif category == 'popular':
                        data = tmdb_service.get_popular_movies(page=page)
                    else:
                        continue
                    
                    if data and 'results' in data:
                        movies_data = data['results']
                        synced_count = MovieDataService.bulk_sync_movies(movies_data)
                        category_movies += synced_count
                        total_movies += synced_count
                        
                        logger.info(f"Synced {synced_count} movies from {category} page {page}")
                    
                except Exception as e:
                    logger.error(f"Error syncing {category} page {page}: {e}")
                    continue
            
            logger.info(f"Synced {category_movies} {category} movies")
        
        # Clear relevant caches
        cache.delete_many([
            'trending_movies_*',
            'popular_movies_*',
            'movie_list_*'
        ])
        
        logger.info(f"TMDb data sync completed. Total movies synced: {total_movies}")
        return f"Successfully synced {total_movies} movies"
        
    except Exception as e:
        logger.error(f"Error in TMDb sync task: {e}")
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries))


@shared_task
def sync_genres_task():
    """Background task to sync genres from TMDb."""
    try:
        logger.info("Starting genres sync")
        synced_count = MovieDataService.sync_genres()
        
        # Clear genres cache
        cache.delete('movie_genres')
        
        logger.info(f"Genres sync completed. Synced {synced_count} genres")
        return f"Successfully synced {synced_count} genres"
        
    except Exception as e:
        logger.error(f"Error in genres sync task: {e}")
        raise


@shared_task
def update_movie_popularity_task():
    """Background task to update movie popularity scores."""
    try:
        from .models import Movie
        from django.db.models import Count, Avg
        
        logger.info("Starting movie popularity update")
        
        # Update popularity based on recent ratings and favorites
        movies = Movie.objects.annotate(
            recent_ratings_count=Count('user_ratings'),
            avg_rating=Avg('user_ratings__rating')
        ).filter(recent_ratings_count__gt=0)
        
        updated_count = 0
        for movie in movies:
            # Simple popularity calculation
            rating_factor = (movie.avg_rating or 0) / 10
            activity_factor = min(movie.recent_ratings_count / 100, 1.0)
            
            new_popularity = (rating_factor * 0.6 + activity_factor * 0.4) * 100
            movie.popularity = new_popularity
            movie.save(update_fields=['popularity'])
            updated_count += 1
        
        logger.info(f"Updated popularity for {updated_count} movies")
        return f"Updated popularity for {updated_count} movies"
        
    except Exception as e:
        logger.error(f"Error updating movie popularity: {e}")
        raise
