"""
Views and viewsets for user account management.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets
from .models import UserInvitation, ApiKey
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserInvitationSerializer,
    ApiKeySerializer,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        # Return users from same tenant
        return User.objects.filter(tenant=user.tenant) if user.tenant else User.objects.none()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()

        # Only allow users to change their own password
        if user.id != request.user.id and not request.user.is_superuser:
            return Response(
                {'error': 'You can only change your own password.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Wrong password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Password changed successfully.'})


class UserInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for user invitations."""

    queryset = UserInvitation.objects.all()
    serializer_class = UserInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return UserInvitation.objects.all()
        # Return invitations for user's tenant
        return UserInvitation.objects.filter(tenant=user.tenant) if user.tenant else UserInvitation.objects.none()

    def create(self, request, *args, **kwargs):
        """Create a new invitation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generate token
        token = secrets.token_urlsafe(32)

        # Create invitation
        invitation = serializer.save(
            tenant=request.user.tenant,
            invited_by=request.user,
            invitation_token=token,
            expires_at=timezone.now() + timedelta(days=7),
        )

        # Send invitation email
        try:
            from apps.notifications.services import NotificationService
            NotificationService.send_notification(
                template_type='user_invitation',
                recipient_email=invitation.email,
                context={
                    'invite_url': invitation.get_absolute_url() if hasattr(invitation, 'get_absolute_url') else '',
                    'inviter_name': request.user.get_full_name() or request.user.email,
                }
            )
        except Exception as e:
            logger.warning(f"Could not send invitation email: {e}")

        return Response(
            UserInvitationSerializer(invitation).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an invitation."""
        invitation = self.get_object()
        invitation.cancel()
        return Response({'message': 'Invitation cancelled successfully.'})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def accept(self, request):
        """Accept an invitation using token."""
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Invitation token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invitation = UserInvitation.objects.get(
                invitation_token=token,
                status=UserInvitation.PENDING
            )
        except UserInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired invitation.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.is_expired:
            invitation.status = UserInvitation.EXPIRED
            invitation.save()
            return Response(
                {'error': 'Invitation has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # User must be authenticated
        if not request.user.is_authenticated:
            return Response(
                {'error': 'You must be logged in to accept an invitation.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        invitation.accept(request.user)

        return Response({
            'message': 'Invitation accepted successfully.',
            'tenant': invitation.tenant.name,
            'role': invitation.role,
        })


class ApiKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for API key management."""

    queryset = ApiKey.objects.all()
    serializer_class = ApiKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ApiKey.objects.all()
        # Return API keys for user's tenant
        return ApiKey.objects.filter(tenant=user.tenant) if user.tenant else ApiKey.objects.none()

    def create(self, request, *args, **kwargs):
        """Create a new API key."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generate API key
        key = secrets.token_urlsafe(32)
        prefix = key[:8]

        # Create API key
        api_key = serializer.save(
            user=request.user,
            tenant=request.user.tenant,
            key=key,
            prefix=prefix,
        )

        # Return the full key only once (during creation)
        response_data = ApiKeySerializer(api_key).data
        response_data['key'] = key  # Include full key only in creation response

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an API key."""
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save()
        return Response({'message': 'API key deactivated successfully.'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an API key."""
        api_key = self.get_object()
        api_key.is_active = True
        api_key.save()
        return Response({'message': 'API key activated successfully.'})
