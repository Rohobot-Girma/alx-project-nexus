# test_tmdb.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommendation.settings')
django.setup()

from movies.services import TMDBService

def test_tmdb_connection():
    try:
        tmdb_service = TMDBService()
        print("Testing TMDB connection...")
        
        # Test basic movie details
        movie_data = tmdb_service.get_movie_details(27205)
        
        if movie_data:
            print("✅ TMDB API connection successful!")
            print(f"Movie title: {movie_data.get('title')}")
            print(f"Movie ID: {movie_data.get('id')}")
        else:
            print("❌ TMDB API returned no data")
            
    except Exception as e:
        print(f"❌ TMDB API error: {e}")

if __name__ == "__main__":
    test_tmdb_connection()