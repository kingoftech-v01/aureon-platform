"""
Custom user models for authentication and account management.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Supports role-based permissions.
    """

    # User Roles
    ADMIN = 'admin'
    MANAGER = 'manager'
    CONTRIBUTOR = 'contributor'
    CLIENT = 'client'  # External client user (read-only portal access)

    ROLE_CHOICES = [
        (ADMIN, _('Admin - Full Access')),
        (MANAGER, _('Manager - Manage Contracts & Invoices')),
        (CONTRIBUTOR, _('Contributor - Limited Access')),
        (CLIENT, _('Client - Portal Access Only')),
    ]

    # UUID for API identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Override username to make it optional
    username = models.CharField(
        _('Username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Optional. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
    )

    # Email as primary identifier
    email = models.EmailField(
        _('Email Address'),
        unique=True,
        help_text=_('Primary email address for authentication')
    )

    # Role & Permissions
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=CONTRIBUTOR,
        help_text=_('User role within the organization')
    )

    # Profile Information
    full_name = models.CharField(
        _('Full Name'),
        max_length=255,
        blank=True,
        help_text=_('User full name')
    )

    phone = PhoneNumberField(
        _('Phone Number'),
        blank=True,
        null=True,
        help_text=_('Contact phone number')
    )

    job_title = models.CharField(
        _('Job Title'),
        max_length=100,
        blank=True,
        help_text=_('User job title or position')
    )

    avatar = models.ImageField(
        _('Avatar'),
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('Profile picture')
    )

    # Preferences
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='UTC',
        help_text=_('User preferred timezone')
    )

    language = models.CharField(
        _('Language'),
        max_length=10,
        default='en',
        help_text=_('Preferred language code')
    )

    # Notification Preferences
    email_notifications = models.BooleanField(
        _('Email Notifications'),
        default=True,
        help_text=_('Receive email notifications')
    )

    sms_notifications = models.BooleanField(
        _('SMS Notifications'),
        default=False,
        help_text=_('Receive SMS notifications')
    )

    # Security
    two_factor_enabled = models.BooleanField(
        _('Two-Factor Authentication'),
        default=False,
        help_text=_('Enable 2FA for enhanced security')
    )

    two_factor_secret = models.CharField(
        _('2FA Secret Key'),
        max_length=32,
        blank=True,
        help_text=_('TOTP secret key for 2FA')
    )

    two_factor_backup_codes = models.JSONField(
        _('2FA Backup Codes'),
        default=list,
        blank=True,
        help_text=_('Backup codes for 2FA recovery')
    )

    last_login_ip = models.GenericIPAddressField(
        _('Last Login IP'),
        blank=True,
        null=True,
        help_text=_('IP address of last login')
    )

    # Status
    is_verified = models.BooleanField(
        _('Email Verified'),
        default=False,
        help_text=_('Whether email has been verified')
    )

    verified_at = models.DateTimeField(
        _('Verified At'),
        blank=True,
        null=True,
        help_text=_('When email was verified')
    )

    # Metadata
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional user metadata in JSON format')
    )

    # Override username requirement
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        """Override save to generate username from email if not provided."""
        if not self.username:
            self.username = self.email.split('@')[0] + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def get_full_name(self):
        """Return the user's full name."""
        if self.full_name:
            return self.full_name
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        """Return the user's short name."""
        return self.first_name or self.email.split('@')[0]

    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_manager(self):
        """Check if user has manager role or higher."""
        return self.role in [self.ADMIN, self.MANAGER] or self.is_superuser

    @property
    def is_client_user(self):
        """Check if user is a client (external user)."""
        return self.role == self.CLIENT

    def can_manage_contracts(self):
        """Check if user can manage contracts."""
        return self.role in [self.ADMIN, self.MANAGER] or self.is_superuser

    def can_manage_invoices(self):
        """Check if user can manage invoices."""
        return self.role in [self.ADMIN, self.MANAGER] or self.is_superuser

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == self.ADMIN or self.is_superuser

    def can_access_analytics(self):
        """Check if user can access analytics."""
        return self.role in [self.ADMIN, self.MANAGER] or self.is_superuser


class UserInvitation(models.Model):
    """
    User invitation model for inviting new team members.
    """

    # Invitation Status
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (ACCEPTED, _('Accepted')),
        (EXPIRED, _('Expired')),
        (CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(
        _('Email Address'),
        help_text=_('Email address to send invitation to')
    )

    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=User.ROLE_CHOICES,
        default=User.CONTRIBUTOR,
        help_text=_('Role to assign upon acceptance')
    )

    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text=_('User who sent the invitation')
    )

    invitation_token = models.CharField(
        _('Invitation Token'),
        max_length=255,
        unique=True,
        help_text=_('Unique token for invitation link')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'), help_text=_('When the invitation expires'))
    accepted_at = models.DateTimeField(_('Accepted At'), blank=True, null=True)

    # Optional message
    message = models.TextField(
        _('Invitation Message'),
        blank=True,
        help_text=_('Optional message to include in invitation email')
    )

    class Meta:
        verbose_name = _('User Invitation')
        verbose_name_plural = _('User Invitations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['invitation_token']),
        ]

    def __str__(self):
        return f"Invitation to {self.email} ({self.status})"

    @property
    def is_expired(self):
        """Check if invitation has expired."""
        from django.utils import timezone
        if self.status == self.ACCEPTED:
            return False
        return timezone.now() > self.expires_at

    def accept(self, user):
        """Mark invitation as accepted."""
        from django.utils import timezone
        self.status = self.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

        # Assign role to user
        user.role = self.role
        user.save()

    def cancel(self):
        """Cancel the invitation."""
        self.status = self.CANCELLED
        self.save()


class ApiKey(models.Model):
    """
    API key model for API authentication.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_keys',
        help_text=_('User who owns this API key')
    )

    name = models.CharField(
        _('Key Name'),
        max_length=100,
        help_text=_('Descriptive name for this API key')
    )

    key = models.CharField(
        _('API Key'),
        max_length=255,
        unique=True,
        help_text=_('The actual API key (hashed)')
    )

    prefix = models.CharField(
        _('Key Prefix'),
        max_length=10,
        help_text=_('First few characters of key for identification')
    )

    # Permissions
    scopes = models.JSONField(
        _('Scopes'),
        default=list,
        help_text=_('List of allowed API scopes/permissions')
    )

    # Status
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether the API key is active')
    )

    # Usage tracking
    last_used_at = models.DateTimeField(
        _('Last Used At'),
        blank=True,
        null=True,
        help_text=_('When the key was last used')
    )

    usage_count = models.PositiveIntegerField(
        _('Usage Count'),
        default=0,
        help_text=_('Number of times the key has been used')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(
        _('Expires At'),
        blank=True,
        null=True,
        help_text=_('Optional expiration date')
    )

    class Meta:
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.prefix}***)"

    @property
    def is_expired(self):
        """Check if API key has expired."""
        from django.utils import timezone
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def record_usage(self):
        """Record API key usage."""
        from django.utils import timezone
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.save(update_fields=['last_used_at', 'usage_count'])


class Team(models.Model):
    """
    Team model for organizing users into groups.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        _('Team Name'),
        max_length=255,
        help_text=_('Name of the team')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Team description')
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_teams',
        help_text=_('User who owns this team')
    )

    is_active = models.BooleanField(
        _('Active'),
        default=True
    )

    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        """Return the number of team members."""
        return self.members.count()


class TeamMember(models.Model):
    """
    Team membership model linking users to teams with roles.
    """

    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    VIEWER = 'viewer'

    ROLE_CHOICES = [
        (OWNER, _('Owner')),
        (ADMIN, _('Admin')),
        (MEMBER, _('Member')),
        (VIEWER, _('Viewer')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members',
        help_text=_('Team this membership belongs to')
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        help_text=_('User who is a member')
    )

    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=MEMBER
    )

    joined_at = models.DateTimeField(
        _('Joined At'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Team Member')
        verbose_name_plural = _('Team Members')
        unique_together = ['team', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.team.name} ({self.role})"


class TeamInvitation(models.Model):
    """
    Invitation to join a team.
    """

    PENDING = 'pending'
    ACCEPTED = 'accepted'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (ACCEPTED, _('Accepted')),
        (EXPIRED, _('Expired')),
        (CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text=_('Team this invitation is for')
    )

    email = models.EmailField(
        _('Email Address'),
        help_text=_('Email address to invite')
    )

    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=TeamMember.ROLE_CHOICES,
        default=TeamMember.MEMBER
    )

    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_team_invitations',
        help_text=_('User who sent the invitation')
    )

    invitation_token = models.CharField(
        _('Invitation Token'),
        max_length=255,
        unique=True
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    accepted_at = models.DateTimeField(_('Accepted At'), null=True, blank=True)

    class Meta:
        verbose_name = _('Team Invitation')
        verbose_name_plural = _('Team Invitations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['team', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['invitation_token']),
        ]

    def __str__(self):
        return f"Team invite to {self.email} for {self.team.name} ({self.status})"

    @property
    def is_expired(self):
        """Check if invitation has expired."""
        from django.utils import timezone
        if self.status == self.ACCEPTED:
            return False
        return timezone.now() > self.expires_at

    def accept(self, user):
        """Accept the team invitation."""
        from django.utils import timezone
        self.status = self.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

        TeamMember.objects.get_or_create(
            team=self.team,
            user=user,
            defaults={'role': self.role}
        )

    def cancel(self):
        """Cancel the invitation."""
        self.status = self.CANCELLED
        self.save()
