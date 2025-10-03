from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    
    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]
