"""
Background tasks for recommendation generation and cache management.
"""

from celery import shared_task
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Recommendation, RecommendationCache
from .algorithms import recommendation_engine

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def generate_user_recommendations_task(user_id=None):
    """
    Background task to generate recommendations for users.
    
    Args:
        user_id: Specific user ID to generate recommendations for (optional)
    """
    try:
        if user_id:
            users = User.objects.filter(id=user_id)
        else:
            # Get active users who have ratings or favorites
            users = User.objects.filter(
                movie_ratings__isnull=False
            ).distinct()[:100]  # Limit to 100 users per run
        
        generated_count = 0
        
        for user in users:
            try:
                # Clear existing recommendations
                Recommendation.objects.filter(
                    user=user,
                    recommendation_type='hybrid'
                ).delete()
                
                # Generate new recommendations
                recommendations_data = recommendation_engine.get_recommendations(user, 20)
                
                # Create recommendation objects
                recommendations = []
                for movie, score, reason in recommendations_data:
                    recommendation = Recommendation(
                        user=user,
                        movie=movie,
                        recommendation_type='hybrid',
                        score=score,
                        reason=reason,
                        metadata={'algorithm': 'hybrid_engine', 'generated_at': timezone.now().isoformat()},
                        expires_at=timezone.now() + timedelta(days=7)
                    )
                    recommendations.append(recommendation)
                
                # Bulk create recommendations
                if recommendations:
                    Recommendation.objects.bulk_create(recommendations)
                    generated_count += len(recommendations)
                
                # Clear user's recommendation cache
                cache.delete(f"user_recommendations_{user.id}_*")
                
                logger.info(f"Generated {len(recommendations)} recommendations for user {user.id}")
                
            except Exception as e:
                logger.error(f"Error generating recommendations for user {user.id}: {e}")
                continue
        
        logger.info(f"Recommendation generation completed. Generated {generated_count} recommendations")
        return f"Generated {generated_count} recommendations for {len(users)} users"
        
    except Exception as e:
        logger.error(f"Error in recommendation generation task: {e}")
        raise


@shared_task
def cleanup_expired_cache_task():
    """Background task to clean up expired cache entries."""
    try:
        logger.info("Starting cache cleanup")
        
        # Clean up expired recommendations
        expired_recommendations = Recommendation.objects.filter(
            expires_at__lt=timezone.now()
        )
        expired_count = expired_recommendations.count()
        expired_recommendations.delete()
        
        # Clean up expired recommendation cache
        expired_cache = RecommendationCache.objects.filter(
            expires_at__lt=timezone.now()
        )
        cache_count = expired_cache.count()
        expired_cache.delete()
        
        # Clear Redis cache patterns (this would need to be implemented based on cache keys)
        # For now, we'll just log the cleanup
        
        logger.info(f"Cache cleanup completed. Removed {expired_count} recommendations and {cache_count} cache entries")
        return f"Cleaned up {expired_count} recommendations and {cache_count} cache entries"
        
    except Exception as e:
        logger.error(f"Error in cache cleanup task: {e}")
        raise


@shared_task
def update_user_similarity_matrix_task():
    """Background task to update user similarity matrix."""
    try:
        from .algorithms import CollaborativeFiltering
        
        logger.info("Starting user similarity matrix update")
        
        # Clear existing similarity cache
        cache.delete("user_similarity_matrix")
        
        # Regenerate similarity matrix
        collab_filter = CollaborativeFiltering()
        similarity_matrix = collab_filter.get_user_similarity_matrix()
        
        logger.info(f"Updated user similarity matrix for {len(similarity_matrix)} users")
        return f"Updated similarity matrix for {len(similarity_matrix)} users"
        
    except Exception as e:
        logger.error(f"Error updating user similarity matrix: {e}")
        raise


@shared_task
def generate_trending_recommendations_task():
    """Background task to generate trending recommendations."""
    try:
        from movies.services import TMDBService, MovieDataService
        from movies.serializers import MovieListSerializer
        
        logger.info("Starting trending recommendations generation")
        
        # Get trending movies from TMDb
        tmdb_service = TMDBService()
        tmdb_data = tmdb_service.get_trending_movies(page=1, time_window='week')
        
        if not tmdb_data:
            logger.warning("No trending data received from TMDb")
            return "No trending data available"
        
        # Sync movies to database
        movies_data = tmdb_data.get('results', [])[:20]
        synced_movies = []
        for movie_data in movies_data:
            movie = MovieDataService.create_or_update_movie(movie_data)
            if movie:
                synced_movies.append(movie)
        
        # Create trending recommendations
        recommendations = []
        for movie in synced_movies:
            recommendation = Recommendation(
                user=None,  # General recommendations
                movie=movie,
                recommendation_type='trending',
                score=0.9,
                reason="Currently trending on TMDb",
                metadata={'source': 'tmdb_trending'},
                expires_at=timezone.now() + timedelta(hours=24)
            )
            recommendations.append(recommendation)
        
        # Clear existing trending recommendations
        Recommendation.objects.filter(
            user__isnull=True,
            recommendation_type='trending'
        ).delete()
        
        # Create new trending recommendations
        if recommendations:
            Recommendation.objects.bulk_create(recommendations)
        
        # Clear trending cache
        cache.delete("trending_recommendations_*")
        
        logger.info(f"Generated {len(recommendations)} trending recommendations")
        return f"Generated {len(recommendations)} trending recommendations"
        
    except Exception as e:
        logger.error(f"Error generating trending recommendations: {e}")
        raise
