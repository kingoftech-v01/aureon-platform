"""
Serializers for the proposals app.
"""

from rest_framework import serializers
from .models import Proposal, ProposalSection, ProposalPricingOption, ProposalActivity


class ProposalSectionSerializer(serializers.ModelSerializer):
    """
    Serializer for proposal sections.
    """

    class Meta:
        model = ProposalSection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProposalPricingOptionSerializer(serializers.ModelSerializer):
    """
    Serializer for proposal pricing options.
    """

    class Meta:
        model = ProposalPricingOption
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProposalActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for proposal activities (read-only).
    """
    user_name = serializers.SerializerMethodField()
    ip_address = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = ProposalActivity
        fields = '__all__'
        read_only_fields = [
            'id', 'proposal', 'activity_type', 'description',
            'user', 'ip_address', 'metadata', 'created_at'
        ]

    def get_user_name(self, obj):
        """Get user full name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return None


class ProposalListSerializer(serializers.ModelSerializer):
    """
    Serializer for proposal list view (minimal fields).
    """
    client_name = serializers.SerializerMethodField()
    client_id = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    sections_count = serializers.SerializerMethodField()
    pricing_options_count = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            'id', 'proposal_number', 'title', 'client', 'client_id',
            'client_name', 'status', 'total_value', 'currency',
            'valid_until', 'created_at', 'is_expired',
            'sections_count', 'pricing_options_count'
        ]
        read_only_fields = ['id', 'proposal_number', 'created_at']

    def get_client_name(self, obj):
        """Get client display name."""
        return obj.client.get_display_name()

    def get_client_id(self, obj):
        """Get client id."""
        return str(obj.client.id)

    def get_sections_count(self, obj):
        """Get the number of sections in the proposal."""
        return obj.sections.count()

    def get_pricing_options_count(self, obj):
        """Get the number of pricing options in the proposal."""
        return obj.pricing_options.count()


class ProposalDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for proposal detail view.
    """
    sections = ProposalSectionSerializer(many=True, read_only=True)
    pricing_options = ProposalPricingOptionSerializer(many=True, read_only=True)
    activities = ProposalActivitySerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    owner_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = '__all__'
        read_only_fields = [
            'id', 'proposal_number', 'created_at', 'updated_at'
        ]

    def get_owner_name(self, obj):
        """Get owner full name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return None

    def get_client_name(self, obj):
        """Get client display name."""
        return obj.client.get_display_name()


class ProposalCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating proposals.
    """

    class Meta:
        model = Proposal
        fields = [
            'id', 'proposal_number', 'title', 'description', 'client',
            'valid_until', 'total_value', 'currency', 'metadata'
        ]
        read_only_fields = ['id', 'proposal_number']

    def validate(self, data):
        """Validate proposal data."""
        # Validate valid_until is in the future for new proposals
        if self.instance is None and data.get('valid_until'):
            from django.utils import timezone
            if data['valid_until'] < timezone.now().date():
                raise serializers.ValidationError({
                    'valid_until': 'Valid until date must be in the future.'
                })

        return data


class ProposalStatsSerializer(serializers.Serializer):
    """
    Serializer for proposal statistics.
    """
    total = serializers.IntegerField()
    by_status = serializers.DictField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    conversion_rate = serializers.FloatField()
