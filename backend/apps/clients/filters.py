"""
Filters for the clients app.
"""

import django_filters
from .models import Client


class ClientFilter(django_filters.FilterSet):
    """
    Filter class for Client model.

    Allows filtering by various fields including lifecycle stage,
    client type, active status, and more.
    """

    # Lifecycle stage filter
    lifecycle_stage = django_filters.MultipleChoiceFilter(
        choices=Client.STAGE_CHOICES,
        label='Lifecycle Stage'
    )

    # Client type filter
    client_type = django_filters.ChoiceFilter(
        choices=Client.TYPE_CHOICES,
        label='Client Type'
    )

    # Active status filter
    is_active = django_filters.BooleanFilter(
        label='Is Active'
    )

    # Owner filter
    owner = django_filters.UUIDFilter(
        field_name='owner__id',
        label='Owner ID'
    )

    # Tags filter (contains any of the provided tags)
    tags = django_filters.CharFilter(
        method='filter_by_tags',
        label='Tags (comma-separated)'
    )

    # Financial filters
    min_total_value = django_filters.NumberFilter(
        field_name='total_value',
        lookup_expr='gte',
        label='Minimum Total Value'
    )

    max_total_value = django_filters.NumberFilter(
        field_name='total_value',
        lookup_expr='lte',
        label='Maximum Total Value'
    )

    has_outstanding_balance = django_filters.BooleanFilter(
        method='filter_outstanding_balance',
        label='Has Outstanding Balance'
    )

    # Date filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )

    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created Before'
    )

    class Meta:
        model = Client
        fields = [
            'lifecycle_stage',
            'client_type',
            'is_active',
            'owner',
            'tags',
        ]

    def filter_by_tags(self, queryset, name, value):
        """Filter by tags (comma-separated list)."""
        if not value:
            return queryset

        tags = [tag.strip() for tag in value.split(',')]
        # Filter clients that have any of the provided tags
        return queryset.filter(tags__overlap=tags)

    def filter_outstanding_balance(self, queryset, name, value):
        """Filter clients with outstanding balance."""
        if value:
            return queryset.filter(outstanding_balance__gt=0)
        else:
            return queryset.filter(outstanding_balance=0)
