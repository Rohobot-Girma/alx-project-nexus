from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Movie endpoints
    path('trending/', views.TrendingMoviesView.as_view(), name='trending-movies'),
    path('popular/', views.PopularMoviesView.as_view(), name='popular-movies'),
    path('search/', views.MovieSearchView.as_view(), name='movie-search'),
    path('list/', views.MovieListView.as_view(), name='movie-list'),
    path('genres/', views.GenreListView.as_view(), name='genre-list'),
    path('<int:tmdb_id>/', views.MovieDetailView.as_view(), name='movie-detail'),
    
    # User favorites
    path('favorites/', views.UserFavoritesView.as_view(), name='user-favorites'),
    path('favorites/<int:pk>/remove/', views.RemoveFavoriteView.as_view(), name='remove-favorite'),
    
    # User ratings
    path('rate/', views.MovieRatingView.as_view(), name='movie-rate'),
    path('ratings/', views.user_ratings_view, name='user-ratings'),
]
