"""
Serializers for user account models.
"""

import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserInvitation, ApiKey, Team, TeamMember, TeamInvitation


def strip_html_tags(value):
    """Strip HTML tags from a string value for XSS prevention."""
    if value:
        return re.sub(r'<[^>]*>', '', value)
    return value

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    full_name = serializers.SerializerMethodField()
    is_admin = serializers.BooleanField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'first_name',
            'last_name',
            'phone',
            'job_title',
            'avatar',
            'role',
            'is_admin',
            'is_manager',
            'timezone',
            'language',
            'email_notifications',
            'sms_notifications',
            'two_factor_enabled',
            'is_verified',
            'is_active',
            'last_login',
            'date_joined',
        ]
        read_only_fields = [
            'id',
            'username',
            'is_verified',
            'last_login',
            'date_joined',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone',
            'role',
        ]

    def validate_first_name(self, value):
        """Strip HTML tags from first_name to prevent XSS."""
        return strip_html_tags(value)

    def validate_last_name(self, value):
        """Strip HTML tags from last_name to prevent XSS."""
        return strip_html_tags(value)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Ensure username is set (defaults to email for AbstractUser compatibility)
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email']
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'job_title',
            'avatar',
            'timezone',
            'language',
            'email_notifications',
            'sms_notifications',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords don't match."})
        return attrs


class UserInvitationSerializer(serializers.ModelSerializer):
    """Serializer for UserInvitation model."""

    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserInvitation
        fields = [
            'id',
            'email',
            'role',
            'status',
            'invited_by',
            'invited_by_email',
            'is_expired',
            'message',
            'created_at',
            'expires_at',
            'accepted_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'invitation_token',
            'invited_by',
            'created_at',
            'expires_at',
            'accepted_at',
        ]


class ApiKeySerializer(serializers.ModelSerializer):
    """Serializer for ApiKey model."""

    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = ApiKey
        fields = [
            'id',
            'name',
            'prefix',
            'scopes',
            'is_active',
            'is_valid',
            'is_expired',
            'last_used_at',
            'usage_count',
            'created_at',
            'expires_at',
        ]
        read_only_fields = [
            'id',
            'prefix',
            'is_valid',
            'is_expired',
            'last_used_at',
            'usage_count',
            'created_at',
        ]


# --- Team Serializers ---

class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for team members."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'user', 'user_email', 'user_name', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name()


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for team list view."""
    owner_name = serializers.SerializerMethodField()
    member_count = serializers.ReadOnlyField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'owner', 'owner_name',
            'is_active', 'member_count', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        return obj.owner.get_full_name()


class TeamDetailSerializer(serializers.ModelSerializer):
    """Serializer for team detail with members."""
    owner_name = serializers.SerializerMethodField()
    member_count = serializers.ReadOnlyField()
    members = TeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'owner', 'owner_name',
            'is_active', 'member_count', 'members', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        return obj.owner.get_full_name()


class TeamCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating teams."""

    class Meta:
        model = Team
        fields = ['name', 'description', 'is_active', 'metadata']


class TeamInvitationSerializer(serializers.ModelSerializer):
    """Serializer for team invitations."""
    invited_by_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = TeamInvitation
        fields = [
            'id', 'team', 'team_name', 'email', 'role', 'invited_by',
            'invited_by_name', 'status', 'is_expired', 'created_at',
            'expires_at', 'accepted_at'
        ]
        read_only_fields = [
            'id', 'invited_by', 'status', 'invitation_token',
            'created_at', 'expires_at', 'accepted_at'
        ]

    def get_invited_by_name(self, obj):
        return obj.invited_by.get_full_name()

    def get_team_name(self, obj):
        return obj.team.name
