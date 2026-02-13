"""
Serializers for the clients app.
"""

from rest_framework import serializers
from .models import Client, ClientNote, ClientDocument
from apps.accounts.models import User


class ClientListSerializer(serializers.ModelSerializer):
    """
    Serializer for client list view (minimal fields for performance).
    """
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'client_type', 'company_name', 'first_name', 'last_name',
            'email', 'phone', 'lifecycle_stage', 'total_value', 'total_paid',
            'outstanding_balance', 'owner', 'owner_name', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_owner_name(self, obj):
        """Get owner full name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return None


class ClientDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for client detail view.
    """
    owner_name = serializers.SerializerMethodField()
    portal_user_email = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    payment_status = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'total_value',
            'total_paid', 'outstanding_balance'
        ]

    def get_owner_name(self, obj):
        """Get owner full name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return None

    def get_portal_user_email(self, obj):
        """Get portal user email."""
        if obj.portal_user:
            return obj.portal_user.email
        return None

    def get_display_name(self, obj):
        """Get display name."""
        return obj.get_display_name()

    def get_full_name(self, obj):
        """Get full name."""
        return obj.get_full_name()


class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating clients.
    """

    class Meta:
        model = Client
        fields = [
            'id', 'client_type', 'company_name', 'first_name', 'last_name',
            'email', 'phone', 'secondary_email', 'secondary_phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'industry', 'company_size', 'annual_revenue', 'tax_id',
            'lifecycle_stage', 'source', 'tags', 'owner', 'portal_access_enabled',
            'notes', 'is_active', 'metadata'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """Validate client data."""
        # If client type is company, ensure company_name is provided
        if data.get('client_type') == Client.COMPANY:
            if not data.get('company_name'):
                raise serializers.ValidationError({
                    'company_name': 'Company name is required for company clients.'
                })

        return data


class ClientNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for client notes.
    """
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ClientNote
        fields = '__all__'
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        """Get author full name."""
        return f"{obj.author.first_name} {obj.author.last_name}"

    def create(self, validated_data):
        """Set author to current user on create."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ClientDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for client documents.
    """
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_by', 'file_size', 'file_type', 'created_at']

    def get_uploaded_by_name(self, obj):
        """Get uploader full name."""
        return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}"

    def get_file_url(self, obj):
        """Get file URL."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def create(self, validated_data):
        """Set uploaded_by to current user on create."""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class ClientStatsSerializer(serializers.Serializer):
    """
    Serializer for client statistics.
    """
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    leads = serializers.IntegerField()
    prospects = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
