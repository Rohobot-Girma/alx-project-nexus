from django.core.management.base import BaseCommand
from django.conf import settings
from movies.services import TMDBService, MovieDataService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to sync movie data from TMDb API.
    """
    help = 'Sync movie data from TMDb API to local database'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to fetch for each category (default: 5)'
        )
        parser.add_argument(
            '--categories',
            nargs='+',
            default=['trending', 'popular'],
            choices=['trending', 'popular'],
            help='Categories to sync (default: trending, popular)'
        )
        parser.add_argument(
            '--genres',
            action='store_true',
            help='Also sync genres from TMDb'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        if not settings.TMDB_API_KEY:
            self.stdout.write(
                self.style.ERROR('TMDb API key not configured. Please set TMDB_API_KEY in settings.')
            )
            return
        
        pages = options['pages']
        categories = options['categories']
        sync_genres = options['genres']
        
        self.stdout.write('Starting TMDb data sync...')
        
        tmdb_service = TMDBService()
        total_movies = 0
        
        # Sync genres first if requested
        if sync_genres:
            self.stdout.write('Syncing genres...')
            synced_genres = MovieDataService.sync_genres()
            self.stdout.write(
                self.style.SUCCESS(f'Synced {synced_genres} new genres')
            )
        
        # Sync movies by category
        for category in categories:
            self.stdout.write(f'Syncing {category} movies...')
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
                        
                        self.stdout.write(f'  Page {page}: {synced_count} movies synced')
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  Page {page}: No data received')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Page {page}: Error - {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Synced {category_movies} {category} movies')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total movies synced: {total_movies}')
        )
        self.stdout.write('TMDb data sync completed!')
