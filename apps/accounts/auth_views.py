"""
JWT Authentication views for login, register, token refresh.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserCreateSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user data."""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user data to the response
        data['user'] = UserSerializer(self.user).data

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view that returns user data with tokens."""
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user account.

    Expects:
    {
        "email": "user@example.com",
        "password": "securepassword",
        "password_confirm": "securepassword",
        "first_name": "John",
        "last_name": "Doe"
    }

    Returns JWT tokens and user data.
    """
    serializer = UserCreateSerializer(data=request.data)

    if serializer.is_valid():
        # Create user (username defaults to email for AbstractUser compatibility)
        user = User.objects.create_user(
            username=serializer.validated_data['email'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', ''),
            phone=serializer.validated_data.get('phone'),
            role=serializer.validated_data.get('role', User.CONTRIBUTOR),
        )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_current_user(request):
    """
    Get current authenticated user.

    Returns user data for the authenticated user.
    """
    if not request.user.is_authenticated:
        return Response({'detail': 'Not authenticated.'}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
def logout(request):
    """
    Logout user by blacklisting the provided refresh token.

    Expects:
    {
        "refresh": "<refresh_token>"
    }

    The refresh token is added to a blacklist so it can no longer be used
    to obtain new access tokens. The client should also discard the access
    token locally.
    """
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_200_OK,
        )
    except Exception:
        return Response(
            {'detail': 'Token is invalid or already blacklisted.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
