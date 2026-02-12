"""
Serializers for the contracts app.
"""

from rest_framework import serializers
from .models import Contract, ContractMilestone
from apps.clients.serializers import ClientListSerializer


class ContractMilestoneSerializer(serializers.ModelSerializer):
    """
    Serializer for contract milestones.
    """
    completed_by_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = ContractMilestone
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_by']

    def get_completed_by_name(self, obj):
        """Get completed by user name."""
        if obj.completed_by:
            return f"{obj.completed_by.first_name} {obj.completed_by.last_name}"
        return None


class ContractListSerializer(serializers.ModelSerializer):
    """
    Serializer for contract list view (minimal fields).
    """
    client_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    is_signed = serializers.ReadOnlyField()
    is_active_period = serializers.ReadOnlyField()

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'client', 'client_name', 'title',
            'contract_type', 'status', 'value', 'currency', 'start_date',
            'end_date', 'is_signed', 'is_active_period', 'completion_percentage',
            'invoiced_amount', 'paid_amount', 'owner', 'owner_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'contract_number', 'created_at', 'updated_at']

    def get_client_name(self, obj):
        """Get client display name."""
        return obj.client.get_display_name()

    def get_owner_name(self, obj):
        """Get owner full name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return None


class ContractDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for contract detail view.
    """
    client = ClientListSerializer(read_only=True)
    milestones = ContractMilestoneSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    is_signed = serializers.ReadOnlyField()
    is_active_period = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()

    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = [
            'id', 'contract_number', 'created_at', 'updated_at',
            'invoiced_amount', 'paid_amount', 'completion_percentage'
        ]

    def get_owner_name(self, obj):
        """Get owner full name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return None


class ContractMilestoneNestedSerializer(serializers.ModelSerializer):
    """
    Serializer for milestones nested inside contract create/update.

    Excludes the ``contract`` foreign key because it is set automatically
    by the parent serializer's ``create`` / ``update`` methods.

    ``id`` is declared as an optional writable field so that callers can
    reference an existing milestone (for update) or omit it (for create).
    """
    id = serializers.UUIDField(required=False)

    class Meta:
        model = ContractMilestone
        exclude = ['contract']
        read_only_fields = ['created_at', 'updated_at', 'completed_by']


class ContractCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating contracts.
    """
    milestones = ContractMilestoneNestedSerializer(many=True, required=False)

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number',
            'client', 'title', 'description', 'contract_type', 'status',
            'start_date', 'end_date', 'value', 'currency', 'hourly_rate',
            'estimated_hours', 'payment_terms', 'invoice_schedule',
            'terms_and_conditions', 'signed_by_client', 'signed_by_company',
            'signature_client', 'signature_company', 'docusign_envelope_id',
            'contract_file', 'owner', 'notes', 'metadata', 'milestones'
        ]
        read_only_fields = ['id', 'contract_number']

    def validate(self, data):
        """Validate contract data."""
        # Validate end date is after start date
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date.'
                })

        # Validate hourly contract has hourly rate
        if data.get('contract_type') == Contract.HOURLY:
            if not data.get('hourly_rate'):
                raise serializers.ValidationError({
                    'hourly_rate': 'Hourly rate is required for hourly contracts.'
                })

        return data

    def create(self, validated_data):
        """Create contract with milestones."""
        milestones_data = validated_data.pop('milestones', [])
        contract = Contract.objects.create(**validated_data)

        # Create milestones
        for milestone_data in milestones_data:
            ContractMilestone.objects.create(contract=contract, **milestone_data)

        return contract

    def update(self, instance, validated_data):
        """Update contract and milestones."""
        milestones_data = validated_data.pop('milestones', None)

        # Update contract fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update milestones if provided
        if milestones_data is not None:
            # Delete existing milestones not in the update
            existing_milestone_ids = [m.get('id') for m in milestones_data if m.get('id')]
            instance.milestones.exclude(id__in=existing_milestone_ids).delete()

            # Update or create milestones
            for milestone_data in milestones_data:
                milestone_id = milestone_data.pop('id', None)
                if milestone_id:
                    ContractMilestone.objects.filter(id=milestone_id).update(**milestone_data)
                else:
                    ContractMilestone.objects.create(contract=instance, **milestone_data)

        return instance


class ContractStatsSerializer(serializers.Serializer):
    """
    Serializer for contract statistics.
    """
    total_contracts = serializers.IntegerField()
    active_contracts = serializers.IntegerField()
    draft_contracts = serializers.IntegerField()
    completed_contracts = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_invoiced = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_completion = serializers.FloatField()
