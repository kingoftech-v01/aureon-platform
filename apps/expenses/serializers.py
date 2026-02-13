"""
Serializers for the expenses app.
"""

from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for expense categories.
    """

    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseListSerializer(serializers.ModelSerializer):
    """
    Serializer for expense list view (minimal fields for performance).
    """
    category = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            'id', 'description', 'amount', 'currency', 'category',
            'expense_date', 'client', 'is_billable', 'is_invoiced',
            'status', 'submitted_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_category(self, obj):
        """Get category id and name."""
        if obj.category:
            return {
                'id': str(obj.category.id),
                'name': obj.category.name,
            }
        return None

    def get_client(self, obj):
        """Get client id and name."""
        if obj.client:
            return {
                'id': str(obj.client.id),
                'name': obj.client.get_display_name(),
            }
        return None

    def get_submitted_by(self, obj):
        """Get submitted_by id and email."""
        if obj.submitted_by:
            return {
                'id': str(obj.submitted_by.id),
                'email': obj.submitted_by.email,
            }
        return None


class ExpenseDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for expense detail view.
    """
    category = ExpenseCategorySerializer(read_only=True)
    is_pending = serializers.ReadOnlyField()

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = [
            'id', 'submitted_by', 'approved_by', 'approved_at',
            'created_at', 'updated_at',
        ]


class ExpenseCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating expenses.
    """

    class Meta:
        model = Expense
        fields = [
            'description', 'amount', 'currency', 'category', 'expense_date',
            'client', 'contract', 'invoice', 'is_billable', 'receipt_file',
            'receipt_number', 'vendor', 'payment_method', 'notes', 'tags',
        ]


class ExpenseStatsSerializer(serializers.Serializer):
    """
    Serializer for expense statistics.
    """
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_billable = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_invoiced = serializers.DecimalField(max_digits=12, decimal_places=2)
    by_category = serializers.ListField(child=serializers.DictField())
    by_status = serializers.DictField()
    by_month = serializers.ListField(child=serializers.DictField())
