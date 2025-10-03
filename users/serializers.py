from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'date_of_birth', 'bio'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        """Create a new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Try to authenticate with email
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password".')


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.ReadOnlyField()
    preferred_genres_display = serializers.ReadOnlyField()
    preferred_languages_display = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'date_of_birth', 'bio', 'avatar',
            'preferred_genres', 'preferred_genres_display',
            'preferred_languages', 'preferred_languages_display',
            'preferred_countries', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def validate_preferred_genres(self, value):
        """Validate preferred genres format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred genres must be a list.")
        
        # Validate that all items are strings
        for genre in value:
            if not isinstance(genre, str):
                raise serializers.ValidationError("All genres must be strings.")
        
        return value
    
    def validate_preferred_languages(self, value):
        """Validate preferred languages format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred languages must be a list.")
        
        # Validate that all items are strings
        for language in value:
            if not isinstance(language, str):
                raise serializers.ValidationError("All languages must be strings.")
        
        return value
    
    def validate_preferred_countries(self, value):
        """Validate preferred countries format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred countries must be a list.")
        
        # Validate that all items are strings
        for country in value:
            if not isinstance(country, str):
                raise serializers.ValidationError("All countries must be strings.")
        
        return value


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user preferences.
    """
    class Meta:
        model = User
        fields = [
            'preferred_genres',
            'preferred_languages',
            'preferred_countries'
        ]
    
    def validate_preferred_genres(self, value):
        """Validate preferred genres."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred genres must be a list.")
        return value
    
    def validate_preferred_languages(self, value):
        """Validate preferred languages."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred languages must be a list.")
        return value
    
    def validate_preferred_countries(self, value):
        """Validate preferred countries."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Preferred countries must be a list.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    old_password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        validators=[validate_password],
        write_only=True
    )
    new_password_confirm = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    
    def validate(self, attrs):
        """Validate password change."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
