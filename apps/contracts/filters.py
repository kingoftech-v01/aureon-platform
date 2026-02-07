"""
Filters for the contracts app.
"""

import django_filters
from django.db.models import Q
from .models import Contract


class ContractFilter(django_filters.FilterSet):
    """
    Filter class for Contract model.
    """

    # Status filter
    status = django_filters.MultipleChoiceFilter(
        choices=Contract.STATUS_CHOICES,
        label='Status'
    )

    # Contract type filter
    contract_type = django_filters.ChoiceFilter(
        choices=Contract.TYPE_CHOICES,
        label='Contract Type'
    )

    # Client filter
    client = django_filters.UUIDFilter(
        field_name='client__id',
        label='Client ID'
    )

    # Owner filter
    owner = django_filters.UUIDFilter(
        field_name='owner__id',
        label='Owner ID'
    )

    # Signature filters
    is_signed = django_filters.BooleanFilter(
        method='filter_is_signed',
        label='Is Fully Signed'
    )

    signed_by_client = django_filters.BooleanFilter(
        label='Signed by Client'
    )

    signed_by_company = django_filters.BooleanFilter(
        label='Signed by Company'
    )

    # Financial filters
    min_value = django_filters.NumberFilter(
        field_name='value',
        lookup_expr='gte',
        label='Minimum Contract Value'
    )

    max_value = django_filters.NumberFilter(
        field_name='value',
        lookup_expr='lte',
        label='Maximum Contract Value'
    )

    # Date filters
    start_date_after = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='gte',
        label='Start Date After'
    )

    start_date_before = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='lte',
        label='Start Date Before'
    )

    end_date_after = django_filters.DateFilter(
        field_name='end_date',
        lookup_expr='gte',
        label='End Date After'
    )

    end_date_before = django_filters.DateFilter(
        field_name='end_date',
        lookup_expr='lte',
        label='End Date Before'
    )

    # Active period filter
    is_active_period = django_filters.BooleanFilter(
        method='filter_active_period',
        label='Is in Active Period'
    )

    class Meta:
        model = Contract
        fields = [
            'status',
            'contract_type',
            'client',
            'owner',
            'signed_by_client',
            'signed_by_company',
        ]

    def filter_is_signed(self, queryset, name, value):
        """Filter fully signed contracts."""
        if value:
            return queryset.filter(signed_by_client=True, signed_by_company=True)
        else:
            return queryset.filter(
                Q(signed_by_client=False) | Q(signed_by_company=False)
            )

    def filter_active_period(self, queryset, name, value):
        """Filter contracts in active date range."""
        from django.utils import timezone
        today = timezone.now().date()

        if value:
            return queryset.filter(
                start_date__lte=today
            ).filter(
                Q(end_date__gte=today) | Q(end_date__isnull=True)
            )
        else:
            return queryset.filter(
                Q(start_date__gt=today) | Q(end_date__lt=today)
            )
