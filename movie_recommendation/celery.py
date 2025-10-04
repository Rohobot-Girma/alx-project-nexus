"""
Celery configuration for the movie recommendation backend.
Handles background tasks for data synchronization and recommendation generation.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommendation.settings')

app = Celery('movie_recommendation')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')


# Periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-tmdb-data': {
        'task': 'movies.tasks.sync_tmdb_data_task',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    'generate-recommendations': {
        'task': 'recommendations.tasks.generate_user_recommendations_task',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
    'cleanup-expired-cache': {
        'task': 'recommendations.tasks.cleanup_expired_cache_task',
        'schedule': crontab(hour=4, minute=0),  # Run daily at 4 AM
    },
}

app.conf.timezone = 'UTC'
