from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Recommendation endpoints
    path('personalized/', views.PersonalizedRecommendationsView.as_view(), name='personalized-recommendations'),
    path('trending/', views.TrendingRecommendationsView.as_view(), name='trending-recommendations'),
    
    # Interaction tracking
    path('track-interaction/', views.track_interaction_view, name='track-interaction'),
]
