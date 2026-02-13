"""
Admin interface for client management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Client, ClientNote, ClientDocument, PortalMessage


class ClientNoteInline(admin.TabularInline):
    """Inline admin for client notes."""
    model = ClientNote
    extra = 0
    fields = ('note_type', 'subject', 'content', 'author', 'created_at')
    readonly_fields = ('created_at',)


class ClientDocumentInline(admin.TabularInline):
    """Inline admin for client documents."""
    model = ClientDocument
    extra = 0
    fields = ('name', 'file', 'uploaded_by', 'created_at')
    readonly_fields = ('created_at', 'file_size')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin interface for Client model."""

    list_display = [
        'get_display_name',
        'email',
        'phone',
        'stage_badge',
        'owner',
        'total_value',
        'outstanding_balance',
        'created_at',
    ]

    list_filter = [
        'client_type',
        'lifecycle_stage',
        'industry',
        'is_active',
        'portal_access_enabled',
        'created_at',
    ]

    search_fields = [
        'first_name',
        'last_name',
        'company_name',
        'email',
        'phone',
    ]

    readonly_fields = [
        'id',
        'total_value',
        'total_paid',
        'outstanding_balance',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        (_('Client Type'), {
            'fields': ('id', 'client_type')
        }),
        (_('Company Information'), {
            'fields': ('company_name', 'industry', 'company_size', 'annual_revenue', 'website'),
            'classes': ('collapse',)
        }),
        (_('Contact Information'), {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'secondary_email',
                'secondary_phone',
            )
        }),
        (_('Address'), {
            'fields': (
                'address_line1',
                'address_line2',
                'city',
                'state',
                'postal_code',
                'country',
            ),
            'classes': ('collapse',)
        }),
        (_('Business Details'), {
            'fields': ('tax_id',)
        }),
        (_('CRM'), {
            'fields': ('lifecycle_stage', 'source', 'tags', 'owner')
        }),
        (_('Financial Summary'), {
            'fields': ('total_value', 'total_paid', 'outstanding_balance'),
            'classes': ('collapse',)
        }),
        (_('Portal Access'), {
            'fields': ('portal_access_enabled', 'portal_user')
        }),
        (_('Notes'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Status & Metadata'), {
            'fields': ('is_active', 'metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ClientNoteInline, ClientDocumentInline]

    def stage_badge(self, obj):
        """Display colored badge for lifecycle stage."""
        colors = {
            Client.LEAD: 'gray',
            Client.PROSPECT: 'blue',
            Client.ACTIVE: 'green',
            Client.INACTIVE: 'orange',
            Client.CHURNED: 'red',
        }
        color = colors.get(obj.lifecycle_stage, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_lifecycle_stage_display()
        )
    stage_badge.short_description = _('Stage')

    actions = ['move_to_active', 'create_portal_access']

    def move_to_active(self, request, queryset):
        """Move clients to active stage."""
        updated = queryset.update(lifecycle_stage=Client.ACTIVE)
        self.message_user(request, f'{updated} client(s) moved to Active stage.')
    move_to_active.short_description = _('Move to Active stage')

    def create_portal_access(self, request, queryset):
        """Create portal access for selected clients."""
        created = 0
        for client in queryset:
            if not client.portal_user:
                client.create_portal_access()
                created += 1
        self.message_user(request, f'Portal access created for {created} client(s).')
    create_portal_access.short_description = _('Create portal access')


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    """Admin interface for ClientNote model."""

    list_display = ['client', 'note_type', 'subject', 'author', 'created_at']
    list_filter = ['note_type', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'client__company_name', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    """Admin interface for ClientDocument model."""

    list_display = ['name', 'client', 'file_type', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['name', 'client__first_name', 'client__last_name', 'client__company_name']
    readonly_fields = ['id', 'file_size', 'created_at']


@admin.register(PortalMessage)
class PortalMessageAdmin(admin.ModelAdmin):
    """Admin for PortalMessage model."""

    list_display = ['subject', 'client', 'sender', 'is_from_client', 'is_read', 'created_at']
    list_filter = ['is_from_client', 'is_read', 'created_at']
    search_fields = ['subject', 'content', 'client__first_name', 'client__last_name', 'client__company_name']
    readonly_fields = ['id', 'read_at', 'created_at', 'updated_at']

    fieldsets = (
        (_('Message Details'), {
            'fields': ('id', 'client', 'sender', 'subject', 'content')
        }),
        (_('Type & Status'), {
            'fields': ('is_from_client', 'is_read', 'read_at')
        }),
        (_('Threading'), {
            'fields': ('parent',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
