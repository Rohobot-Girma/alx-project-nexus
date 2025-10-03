from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserPreferencesSerializer,
    ChangePasswordSerializer
)


class UserRegistrationView(APIView):
    """
    User registration endpoint.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Create a new user account with email and password",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User created successfully",
                examples={
                    "application/json": {
                        "id": 1,
                        "username": "johndoe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "tokens": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad request - validation errors")
        }
    )
    def post(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Login user
            login(request, user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    User login endpoint.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Login user",
        operation_description="Authenticate user with email and password",
        request_body=UserLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "user": {
                            "id": 1,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "first_name": "John",
                            "last_name": "Doe"
                        },
                        "tokens": {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad request - invalid credentials")
        }
    )
    def post(self, request):
        """Login user."""
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Login user
            login(request, user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(RetrieveUpdateAPIView):
    """
    User profile view - get and update user profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the current user."""
        return self.request.user
    
    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Retrieve current user's profile information",
        responses={
            200: UserProfileSerializer,
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request, *args, **kwargs):
        """Get user profile."""
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description="Update current user's profile information",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: openapi.Response(description="Bad request - validation errors"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def patch(self, request, *args, **kwargs):
        """Update user profile."""
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description="Update current user's profile information",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: openapi.Response(description="Bad request - validation errors"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def put(self, request, *args, **kwargs):
        """Update user profile."""
        return super().put(request, *args, **kwargs)


class UserPreferencesView(APIView):
    """
    User preferences view - update movie preferences.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get user preferences",
        operation_description="Retrieve current user's movie preferences",
        responses={
            200: openapi.Response(
                description="User preferences",
                examples={
                    "application/json": {
                        "preferred_genres": ["Action", "Comedy", "Drama"],
                        "preferred_languages": ["en", "es", "fr"],
                        "preferred_countries": ["US", "GB", "FR"]
                    }
                }
            ),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        """Get user preferences."""
        user = request.user
        serializer = UserPreferencesSerializer(user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update user preferences",
        operation_description="Update current user's movie preferences",
        request_body=UserPreferencesSerializer,
        responses={
            200: UserPreferencesSerializer,
            400: openapi.Response(description="Bad request - validation errors"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def patch(self, request):
        """Update user preferences."""
        user = request.user
        serializer = UserPreferencesSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Change password view.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Change password",
        operation_description="Change current user's password",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                examples={
                    "application/json": {
                        "message": "Password changed successfully"
                    }
                }
            ),
            400: openapi.Response(description="Bad request - validation errors"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def post(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@swagger_auto_schema(
    operation_summary="Logout user",
    operation_description="Logout current user and blacklist refresh token",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Refresh token to blacklist'
            )
        },
        required=['refresh']
    ),
    responses={
        200: openapi.Response(
            description="Logout successful",
            examples={
                "application/json": {
                    "message": "Logout successful"
                }
            }
        ),
        400: openapi.Response(description="Bad request - invalid token"),
        401: openapi.Response(description="Authentication required")
    }
)
def logout_view(request):
    """Logout user and blacklist refresh token."""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )