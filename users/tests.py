from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class UserModelTest(TestCase):
    """
    Test cases for User model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'preferred_genres': ['Action', 'Comedy'],
            'preferred_languages': ['en', 'es']
        }
    
    def test_create_user(self):
        """Test user creation."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.preferred_genres, ['Action', 'Comedy'])
        self.assertEqual(user.preferred_languages, ['en', 'es'])
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_full_name_property(self):
        """Test full name property."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')
    
    def test_preferred_genres_display(self):
        """Test preferred genres display."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_preferred_genres_display(), 'Action, Comedy')
    
    def test_preferred_languages_display(self):
        """Test preferred languages display."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_preferred_languages_display(), 'en, es')


class UserAPITest(APITestCase):
    """
    Test cases for User API endpoints.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        self.login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        url = reverse('users:user-register')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['user']['username'], 'testuser')
        
        # Verify user was created in database
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
    
    def test_user_registration_duplicate_email(self):
        """Test user registration with duplicate email."""
        # Create first user
        User.objects.create_user(**{
            'username': 'user1',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        url = reverse('users:user-register')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_registration_password_mismatch(self):
        """Test user registration with password mismatch."""
        self.user_data['password_confirm'] = 'differentpass'
        
        url = reverse('users:user-register')
        response = self.client.post(url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_user_login(self):
        """Test user login endpoint."""
        # Create user first
        User.objects.create_user(**{
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        url = reverse('users:user-login')
        response = self.client.post(url, self.login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials."""
        url = reverse('users:user-login')
        invalid_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_profile_get(self):
        """Test getting user profile."""
        user = User.objects.create_user(**{
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_user_profile_update(self):
        """Test updating user profile."""
        user = User.objects.create_user(**{
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-profile')
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'Updated bio'
        }
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['bio'], 'Updated bio')
    
    def test_user_preferences_update(self):
        """Test updating user preferences."""
        user = User.objects.create_user(**{
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-preferences')
        preferences_data = {
            'preferred_genres': ['Action', 'Comedy', 'Drama'],
            'preferred_languages': ['en', 'es', 'fr'],
            'preferred_countries': ['US', 'GB', 'FR']
        }
        response = self.client.patch(url, preferences_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['preferred_genres'], ['Action', 'Comedy', 'Drama'])
        self.assertEqual(response.data['preferred_languages'], ['en', 'es', 'fr'])
        self.assertEqual(response.data['preferred_countries'], ['US', 'GB', 'FR'])
    
    def test_change_password(self):
        """Test changing user password."""
        user = User.objects.create_user(**{
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:change-password')
        password_data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))
        self.assertFalse(user.check_password('testpass123'))
    
    def test_logout(self):
        """Test user logout."""
        user = User.objects.create_user(**{
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Get JWT token
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-logout')
        logout_data = {
            'refresh': str(refresh)
        }
        response = self.client.post(url, logout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)