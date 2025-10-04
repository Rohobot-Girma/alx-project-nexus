"""
Advanced recommendation algorithms for the movie recommendation system.
Implements collaborative filtering, content-based filtering, and hybrid approaches.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from django.db.models import Q, Count, Avg, F
from django.core.cache import cache
from django.conf import settings

from .models import Recommendation, UserInteraction
from movies.models import Movie, MovieRating, UserFavorite
from users.models import User

logger = logging.getLogger(__name__)


class CollaborativeFiltering:
    """
    Collaborative filtering recommendation algorithm.
    Recommends movies based on user similarity and item-based filtering.
    """
    
    def __init__(self):
        self.min_common_ratings = 5
        self.min_users_per_movie = 10
    
    def get_user_similarity_matrix(self) -> Dict[int, Dict[int, float]]:
        """
        Calculate user similarity matrix using cosine similarity.
        
        Returns:
            Dictionary mapping user_id to similar users with similarity scores
        """
        cache_key = "user_similarity_matrix"
        cached_matrix = cache.get(cache_key)
        
        if cached_matrix:
            logger.info("Returning cached user similarity matrix")
            return cached_matrix
        
        # Get all users with ratings
        users_with_ratings = User.objects.filter(
            movie_ratings__isnull=False
        ).distinct()
        
        similarity_matrix = {}
        
        for user in users_with_ratings:
            user_ratings = dict(
                MovieRating.objects.filter(user=user)
                .values_list('movie_id', 'rating')
            )
            
            if len(user_ratings) < self.min_common_ratings:
                continue
            
            similar_users = {}
            
            for other_user in users_with_ratings:
                if other_user.id == user.id:
                    continue
                
                other_ratings = dict(
                    MovieRating.objects.filter(user=other_user)
                    .values_list('movie_id', 'rating')
                )
                
                if len(other_ratings) < self.min_common_ratings:
                    continue
                
                # Calculate cosine similarity
                similarity = self._calculate_cosine_similarity(
                    user_ratings, other_ratings
                )
                
                if similarity > 0.1:  # Only include meaningful similarities
                    similar_users[other_user.id] = similarity
            
            similarity_matrix[user.id] = similar_users
        
        # Cache for 1 hour
        cache.set(cache_key, similarity_matrix, 3600)
        logger.info(f"Calculated user similarity matrix for {len(similarity_matrix)} users")
        
        return similarity_matrix
    
    def _calculate_cosine_similarity(
        self, ratings1: Dict[int, float], ratings2: Dict[int, float]
    ) -> float:
        """Calculate cosine similarity between two rating vectors."""
        common_movies = set(ratings1.keys()) & set(ratings2.keys())
        
        if len(common_movies) < self.min_common_ratings:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = sum(ratings1[movie] * ratings2[movie] for movie in common_movies)
        
        norm1 = sum(rating ** 2 for rating in ratings1.values()) ** 0.5
        norm2 = sum(rating ** 2 for rating in ratings2.values()) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_recommendations(
        self, user: User, limit: int = 20
    ) -> List[Tuple[Movie, float, str]]:
        """
        Get collaborative filtering recommendations for a user.
        
        Args:
            user: User to get recommendations for
            limit: Maximum number of recommendations
            
        Returns:
            List of tuples (movie, score, reason)
        """
        try:
            similarity_matrix = self.get_user_similarity_matrix()
            
            if user.id not in similarity_matrix:
                logger.info(f"No similar users found for user {user.id}")
                return []
            
            # Get user's rated movies
            user_rated_movies = set(
                MovieRating.objects.filter(user=user)
                .values_list('movie_id', flat=True)
            )
            
            # Calculate predicted ratings for unrated movies
            movie_scores = {}
            
            for similar_user_id, similarity in similarity_matrix[user.id].items():
                similar_user_ratings = MovieRating.objects.filter(
                    user_id=similar_user_id
                ).exclude(movie_id__in=user_rated_movies)
                
                for rating in similar_user_ratings:
                    movie_id = rating.movie_id
                    if movie_id not in movie_scores:
                        movie_scores[movie_id] = {'weighted_sum': 0, 'weight_sum': 0}
                    
                    movie_scores[movie_id]['weighted_sum'] += rating.rating * similarity
                    movie_scores[movie_id]['weight_sum'] += abs(similarity)
            
            # Calculate final scores and get movies
            recommendations = []
            for movie_id, scores in movie_scores.items():
                if scores['weight_sum'] > 0:
                    predicted_rating = scores['weighted_sum'] / scores['weight_sum']
                    
                    try:
                        movie = Movie.objects.get(id=movie_id)
                        recommendations.append((
                            movie,
                            predicted_rating,
                            f"Recommended by users with similar tastes (score: {predicted_rating:.2f})"
                        ))
                    except Movie.DoesNotExist:
                        continue
            
            # Sort by predicted rating and return top recommendations
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {e}")
            return []


class ContentBasedFiltering:
    """
    Content-based filtering recommendation algorithm.
    Recommends movies based on genre and content similarity.
    """
    
    def __init__(self):
        self.genre_weights = {
            # Action and Adventure
            28: 1.0, 12: 1.0, 10752: 1.0,  # Action, Adventure, War
            
            # Drama and Romance
            18: 0.9, 10749: 0.9,  # Drama, Romance
            
            # Comedy and Family
            35: 0.8, 10751: 0.8,  # Comedy, Family
            
            # Thriller and Horror
            53: 0.9, 27: 0.7,  # Thriller, Horror
            
            # Sci-Fi and Fantasy
            878: 1.0, 14: 1.0,  # Science Fiction, Fantasy
            
            # Documentary and Other
            99: 0.6, 10770: 0.5,  # Documentary, TV Movie
        }
    
    def get_recommendations(
        self, user: User, limit: int = 20
    ) -> List[Tuple[Movie, float, str]]:
        """
        Get content-based recommendations for a user.
        
        Args:
            user: User to get recommendations for
            limit: Maximum number of recommendations
            
        Returns:
            List of tuples (movie, score, reason)
        """
        try:
            # Get user's preferred genres and liked movies
            user_genres = user.preferred_genres or []
            user_favorites = UserFavorite.objects.filter(user=user)
            user_ratings = MovieRating.objects.filter(
                user=user, rating__gte=4.0
            ).select_related('movie')
            
            # Build user profile from preferences and history
            user_profile = self._build_user_profile(user_genres, user_ratings)
            
            if not user_profile:
                logger.info(f"No user profile built for user {user.id}")
                return []
            
            # Get movies user hasn't interacted with
            excluded_movies = set()
            excluded_movies.update(
                user_favorites.values_list('movie_id', flat=True)
            )
            excluded_movies.update(
                MovieRating.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            
            # Calculate content similarity scores
            recommendations = []
            
            # Query movies with user's preferred genres
            preferred_genre_ids = self._get_genre_ids(user_genres)
            
            movies = Movie.objects.filter(
                genre_ids__overlap=preferred_genre_ids
            ).exclude(
                id__in=excluded_movies
            ).order_by('-popularity', '-vote_average')[:limit * 3]
            
            for movie in movies:
                similarity_score = self._calculate_content_similarity(
                    user_profile, movie
                )
                
                if similarity_score > 0.1:
                    recommendations.append((
                        movie,
                        similarity_score,
                        f"Similar to your preferred genres: {', '.join(user_genres)}"
                    ))
            
            # Sort by similarity score and return top recommendations
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in content-based filtering: {e}")
            return []
    
    def _build_user_profile(
        self, user_genres: List[str], user_ratings
    ) -> Dict[int, float]:
        """Build user profile from preferences and rating history."""
        profile = {}
        
        # Add genre preferences
        for genre in user_genres:
            genre_id = self._get_genre_id_by_name(genre)
            if genre_id:
                profile[genre_id] = 1.0
        
        # Add weighted preferences from rating history
        for rating in user_ratings:
            for genre_id in rating.movie.genre_ids:
                weight = self.genre_weights.get(genre_id, 0.5)
                normalized_weight = weight * (rating.rating / 5.0)
                
                if genre_id in profile:
                    profile[genre_id] = max(profile[genre_id], normalized_weight)
                else:
                    profile[genre_id] = normalized_weight
        
        return profile
    
    def _calculate_content_similarity(
        self, user_profile: Dict[int, float], movie: Movie
    ) -> float:
        """Calculate content similarity between user profile and movie."""
        if not movie.genre_ids:
            return 0.0
        
        # Calculate weighted genre similarity
        similarity_sum = 0.0
        weight_sum = 0.0
        
        for genre_id in movie.genre_ids:
            if genre_id in user_profile:
                weight = self.genre_weights.get(genre_id, 0.5)
                similarity_sum += user_profile[genre_id] * weight
                weight_sum += weight
        
        if weight_sum == 0:
            return 0.0
        
        # Normalize by movie popularity and rating
        base_score = similarity_sum / weight_sum
        
        # Boost score based on movie quality
        popularity_boost = min(movie.popularity / 100, 1.0)
        rating_boost = min(movie.vote_average / 10, 1.0)
        
        final_score = base_score * (0.6 + 0.2 * popularity_boost + 0.2 * rating_boost)
        
        return min(final_score, 1.0)
    
    def _get_genre_ids(self, genre_names: List[str]) -> List[int]:
        """Convert genre names to TMDb genre IDs."""
        genre_mapping = {
            'Action': 28, 'Adventure': 12, 'Animation': 16, 'Comedy': 35,
            'Crime': 80, 'Documentary': 99, 'Drama': 18, 'Family': 10751,
            'Fantasy': 14, 'History': 36, 'Horror': 27, 'Music': 10402,
            'Mystery': 9648, 'Romance': 10749, 'Science Fiction': 878,
            'TV Movie': 10770, 'Thriller': 53, 'War': 10752, 'Western': 37
        }
        
        return [genre_mapping.get(genre, None) for genre in genre_names if genre in genre_mapping]
    
    def _get_genre_id_by_name(self, genre_name: str) -> Optional[int]:
        """Get TMDb genre ID by name."""
        genre_mapping = {
            'Action': 28, 'Adventure': 12, 'Animation': 16, 'Comedy': 35,
            'Crime': 80, 'Documentary': 99, 'Drama': 18, 'Family': 10751,
            'Fantasy': 14, 'History': 36, 'Horror': 27, 'Music': 10402,
            'Mystery': 9648, 'Romance': 10749, 'Science Fiction': 878,
            'TV Movie': 10770, 'Thriller': 53, 'War': 10752, 'Western': 37
        }
        return genre_mapping.get(genre_name)


class HybridRecommendationEngine:
    """
    Hybrid recommendation engine combining multiple algorithms.
    """
    
    def __init__(self):
        self.collaborative_filter = CollaborativeFiltering()
        self.content_filter = ContentBasedFiltering()
        self.config = settings.RECOMMENDATION_CONFIG
    
    def get_recommendations(
        self, user: User, limit: int = 20
    ) -> List[Tuple[Movie, float, str]]:
        """
        Get hybrid recommendations for a user.
        
        Args:
            user: User to get recommendations for
            limit: Maximum number of recommendations
            
        Returns:
            List of tuples (movie, score, reason)
        """
        try:
            all_recommendations = []
            
            # Get collaborative filtering recommendations
            if user.movie_ratings.count() >= self.config['MIN_RATING_COUNT']:
                collab_recs = self.collaborative_filter.get_recommendations(
                    user, limit // 2
                )
                for movie, score, reason in collab_recs:
                    weighted_score = score * self.config['COLLABORATIVE_WEIGHT']
                    all_recommendations.append((movie, weighted_score, reason))
            
            # Get content-based recommendations
            content_recs = self.content_filter.get_recommendations(
                user, limit // 2
            )
            for movie, score, reason in content_recs:
                weighted_score = score * self.config['CONTENT_BASED_WEIGHT']
                all_recommendations.append((movie, weighted_score, reason))
            
            # Get popularity-based recommendations as fallback
            if len(all_recommendations) < limit:
                popularity_recs = self._get_popularity_recommendations(
                    user, limit - len(all_recommendations)
                )
                all_recommendations.extend(popularity_recs)
            
            # Remove duplicates and sort by score
            unique_recommendations = {}
            for movie, score, reason in all_recommendations:
                if movie.id not in unique_recommendations:
                    unique_recommendations[movie.id] = (movie, score, reason)
                else:
                    # Combine scores for duplicate movies
                    existing_movie, existing_score, existing_reason = unique_recommendations[movie.id]
                    combined_score = max(existing_score, score)
                    unique_recommendations[movie.id] = (movie, combined_score, existing_reason)
            
            # Sort by score and return top recommendations
            final_recommendations = list(unique_recommendations.values())
            final_recommendations.sort(key=lambda x: x[1], reverse=True)
            
            return final_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid recommendation engine: {e}")
            return []
    
    def _get_popularity_recommendations(
        self, user: User, limit: int
    ) -> List[Tuple[Movie, float, str]]:
        """Get popularity-based recommendations as fallback."""
        try:
            # Get movies user hasn't interacted with
            excluded_movies = set()
            excluded_movies.update(
                UserFavorite.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            excluded_movies.update(
                MovieRating.objects.filter(user=user).values_list('movie_id', flat=True)
            )
            
            movies = Movie.objects.filter(
                popularity__gt=10,
                vote_average__gt=6.0,
                vote_count__gt=100
            ).exclude(
                id__in=excluded_movies
            ).order_by('-popularity')[:limit]
            
            recommendations = []
            for movie in movies:
                # Calculate popularity score
                popularity_score = min(movie.popularity / 100, 1.0)
                rating_score = movie.vote_average / 10
                combined_score = (popularity_score * 0.6 + rating_score * 0.4)
                weighted_score = combined_score * self.config['POPULARITY_WEIGHT']
                
                recommendations.append((
                    movie,
                    weighted_score,
                    "Popular movies trending now"
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in popularity recommendations: {e}")
            return []


# Global recommendation engine instance
recommendation_engine = HybridRecommendationEngine()
