"""
Admin interface for user account management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, UserInvitation, ApiKey, Team, TeamMember, TeamInvitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = [
        'email',
        'full_name',
        'role_badge',
        'status_badge',
        'last_login',
    ]

    list_filter = [
        'role',
        'is_active',
        'is_staff',
        'is_verified',
        'two_factor_enabled',
        'date_joined',
    ]

    search_fields = [
        'email',
        'first_name',
        'last_name',
        'full_name',
        'username',
    ]

    readonly_fields = [
        'id',
        'date_joined',
        'last_login',
        'verified_at',
        'last_login_ip',
    ]

    fieldsets = (
        (_('Authentication'), {
            'fields': ('id', 'email', 'username', 'password')
        }),
        (_('Personal Information'), {
            'fields': ('full_name', 'first_name', 'last_name', 'phone', 'job_title', 'avatar')
        }),
        (_('Organization'), {
            'fields': ('role',)
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Preferences'), {
            'fields': ('timezone', 'language', 'email_notifications', 'sms_notifications'),
            'classes': ('collapse',)
        }),
        (_('Security'), {
            'fields': ('two_factor_enabled', 'is_verified', 'verified_at', 'last_login_ip'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )

    ordering = ('-date_joined',)

    def role_badge(self, obj):
        """Display colored badge for user role."""
        colors = {
            User.ADMIN: 'red',
            User.MANAGER: 'orange',
            User.CONTRIBUTOR: 'blue',
            User.CLIENT: 'gray',
        }
        color = colors.get(obj.role, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = _('Role')

    def status_badge(self, obj):
        """Display status badges."""
        badges = []
        if obj.is_active:
            badges.append('<span style="color: green;">✓ Active</span>')
        else:
            badges.append('<span style="color: red;">✗ Inactive</span>')

        if obj.is_verified:
            badges.append('<span style="color: green;">✓ Verified</span>')

        if obj.two_factor_enabled:
            badges.append('<span style="color: blue;">🔒 2FA</span>')

        return format_html(' | '.join(badges))
    status_badge.short_description = _('Status')


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    """Admin interface for UserInvitation model."""

    list_display = [
        'email',
        'role',
        'status_badge',
        'invited_by',
        'created_at',
        'expires_at',
    ]

    list_filter = [
        'status',
        'role',
        'created_at',
    ]

    search_fields = [
        'email',
        'invited_by__email',
    ]

    readonly_fields = [
        'id',
        'invitation_token',
        'created_at',
        'accepted_at',
    ]

    fieldsets = (
        (_('Invitation Details'), {
            'fields': ('id', 'email', 'role')
        }),
        (_('Invitation Status'), {
            'fields': ('status', 'invitation_token', 'invited_by')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'expires_at', 'accepted_at')
        }),
        (_('Message'), {
            'fields': ('message',),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display colored badge for invitation status."""
        colors = {
            UserInvitation.PENDING: 'orange',
            UserInvitation.ACCEPTED: 'green',
            UserInvitation.EXPIRED: 'gray',
            UserInvitation.CANCELLED: 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')

    actions = ['cancel_invitations']

    def cancel_invitations(self, request, queryset):
        """Cancel selected invitations."""
        updated = 0
        for invitation in queryset.filter(status=UserInvitation.PENDING):
            invitation.cancel()
            updated += 1
        self.message_user(request, f'{updated} invitation(s) cancelled.')
    cancel_invitations.short_description = _('Cancel selected invitations')


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """Admin interface for ApiKey model."""

    list_display = [
        'name',
        'prefix_display',
        'user',
        'status_badge',
        'usage_count',
        'last_used_at',
        'created_at',
    ]

    list_filter = [
        'is_active',
        'created_at',
    ]

    search_fields = [
        'name',
        'prefix',
        'user__email',
    ]

    readonly_fields = [
        'id',
        'key',
        'prefix',
        'created_at',
        'last_used_at',
        'usage_count',
    ]

    fieldsets = (
        (_('API Key Information'), {
            'fields': ('id', 'name', 'user')
        }),
        (_('Key Details'), {
            'fields': ('key', 'prefix', 'scopes')
        }),
        (_('Status & Usage'), {
            'fields': ('is_active', 'usage_count', 'last_used_at', 'expires_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def prefix_display(self, obj):
        """Display key prefix."""
        return f"{obj.prefix}***"
    prefix_display.short_description = _('Key')

    def status_badge(self, obj):
        """Display status badge."""
        if not obj.is_valid:
            return format_html('<span style="color: red;">✗ Invalid</span>')
        elif obj.is_expired:
            return format_html('<span style="color: orange;">⚠ Expired</span>')
        else:
            return format_html('<span style="color: green;">✓ Active</span>')
    status_badge.short_description = _('Status')

    actions = ['deactivate_keys', 'activate_keys']

    def deactivate_keys(self, request, queryset):
        """Deactivate selected API keys."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} API key(s) deactivated.')
    deactivate_keys.short_description = _('Deactivate selected keys')

    def activate_keys(self, request, queryset):
        """Activate selected API keys."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} API key(s) activated.')
    activate_keys.short_description = _('Activate selected keys')


class TeamMemberInline(admin.TabularInline):
    """Inline admin for team members."""
    model = TeamMember
    extra = 0
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ('joined_at',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin for Team model."""

    list_display = ['name', 'owner', 'member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'owner__email', 'owner__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [TeamMemberInline]

    fieldsets = (
        (_('Team Information'), {
            'fields': ('id', 'name', 'description', 'owner', 'is_active')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def member_count(self, obj):
        """Display member count."""
        return obj.member_count
    member_count.short_description = _('Members')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin for TeamMember model."""

    list_display = ['team', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['team__name', 'user__email', 'user__full_name']
    readonly_fields = ['joined_at']

    fieldsets = (
        (_('Membership'), {
            'fields': ('team', 'user', 'role')
        }),
        (_('Dates'), {
            'fields': ('joined_at',),
        }),
    )


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    """Admin for TeamInvitation model."""

    list_display = ['team', 'email', 'role', 'status_badge', 'invited_by', 'created_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['email', 'team__name', 'invited_by__email']
    readonly_fields = ['id', 'invitation_token', 'created_at', 'accepted_at']

    fieldsets = (
        (_('Invitation Details'), {
            'fields': ('id', 'team', 'email', 'role')
        }),
        (_('Status'), {
            'fields': ('status', 'invitation_token', 'invited_by')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'expires_at', 'accepted_at')
        }),
    )

    def status_badge(self, obj):
        """Display colored badge for invitation status."""
        colors = {
            'pending': 'orange',
            'accepted': 'green',
            'expired': 'gray',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')

    actions = ['cancel_invitations']

    def cancel_invitations(self, request, queryset):
        """Cancel selected team invitations."""
        updated = 0
        for invitation in queryset.filter(status='pending'):
            invitation.cancel()
            updated += 1
        self.message_user(request, f'{updated} team invitation(s) cancelled.')
    cancel_invitations.short_description = _('Cancel selected invitations')
