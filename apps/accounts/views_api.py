"""
Views and viewsets for user account management.
"""

import logging
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets
from .models import UserInvitation, ApiKey, Team, TeamMember, TeamInvitation
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserInvitationSerializer,
    ApiKeySerializer,
    TeamSerializer,
    TeamDetailSerializer,
    TeamCreateUpdateSerializer,
    TeamMemberSerializer,
    TeamInvitationSerializer,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class IsAdminOrSuperuser(IsAuthenticated):
    """Permission class that only allows admin or superuser access."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if view.action in ['destroy', 'create']:
            return request.user.is_superuser or getattr(request.user, 'role', None) in ['admin']
        return True


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['destroy', 'create']:
            return [IsAdminOrSuperuser()]
        return super().get_permissions()

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
        # Return active users
        return User.objects.filter(is_active=True)

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
        # Return all invitations
        return UserInvitation.objects.all()

    def create(self, request, *args, **kwargs):
        """Create a new invitation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generate token
        token = secrets.token_urlsafe(32)

        # Create invitation
        invitation = serializer.save(
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
        # Return API keys for the current user
        return ApiKey.objects.filter(user=user)

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


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for team management."""

    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TeamDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TeamCreateUpdateSerializer
        return TeamSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Team.objects.all()
        return Team.objects.filter(
            models.Q(owner=user) | models.Q(members__user=user)
        ).distinct()

    def perform_create(self, serializer):
        team = serializer.save(owner=self.request.user)
        # Add creator as owner member
        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role=TeamMember.OWNER
        )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """List team members."""
        team = self.get_object()
        members = team.members.select_related('user').all()
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """Invite a user to the team."""
        team = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', TeamMember.MEMBER)

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = secrets.token_urlsafe(32)
        invitation = TeamInvitation.objects.create(
            team=team,
            email=email,
            role=role,
            invited_by=request.user,
            invitation_token=token,
            expires_at=timezone.now() + timedelta(days=7),
        )

        serializer = TeamInvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the team."""
        team = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = TeamMember.objects.get(team=team, user_id=user_id)
            if member.role == TeamMember.OWNER:
                return Response(
                    {'error': 'Cannot remove the team owner.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            member.delete()
            return Response({'message': 'Member removed successfully.'})
        except TeamMember.DoesNotExist:
            return Response(
                {'error': 'Member not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get team statistics."""
        queryset = self.get_queryset()
        stats_data = {
            'total_teams': queryset.count(),
            'active_teams': queryset.filter(is_active=True).count(),
            'total_members': TeamMember.objects.filter(team__in=queryset).count(),
        }
        return Response(stats_data)


class TeamMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for team member management."""

    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TeamMember.objects.all().select_related('user', 'team')
        return TeamMember.objects.filter(
            models.Q(team__owner=user) | models.Q(user=user)
        ).select_related('user', 'team').distinct()


class TeamInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for team invitation management."""

    queryset = TeamInvitation.objects.all()
    serializer_class = TeamInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TeamInvitation.objects.all()
        return TeamInvitation.objects.filter(
            models.Q(team__owner=user) | models.Q(invited_by=user) | models.Q(email=user.email)
        ).distinct()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a team invitation."""
        invitation = self.get_object()
        invitation.cancel()
        return Response({'message': 'Invitation cancelled.'})

    @action(detail=False, methods=['post'])
    def accept(self, request):
        """Accept a team invitation."""
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invitation = TeamInvitation.objects.get(
                invitation_token=token,
                status=TeamInvitation.PENDING
            )
        except TeamInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired invitation.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if invitation.is_expired:
            invitation.status = TeamInvitation.EXPIRED
            invitation.save()
            return Response(
                {'error': 'Invitation has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation.accept(request.user)
        return Response({
            'message': 'Team invitation accepted.',
            'team': str(invitation.team.id),
            'role': invitation.role,
        })
