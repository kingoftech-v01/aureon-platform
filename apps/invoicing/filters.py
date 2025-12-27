"""
Filters for the invoicing app.
"""

import django_filters
from .models import Invoice


class InvoiceFilter(django_filters.FilterSet):
    """
    Filter class for Invoice model.
    """

    # Status filter
    status = django_filters.MultipleChoiceFilter(
        choices=Invoice.STATUS_CHOICES,
        label='Status'
    )

    # Client filter
    client = django_filters.UUIDFilter(
        field_name='client__id',
        label='Client ID'
    )

    # Contract filter
    contract = django_filters.UUIDFilter(
        field_name='contract__id',
        label='Contract ID'
    )

    # Financial filters
    min_total = django_filters.NumberFilter(
        field_name='total',
        lookup_expr='gte',
        label='Minimum Total'
    )

    max_total = django_filters.NumberFilter(
        field_name='total',
        lookup_expr='lte',
        label='Maximum Total'
    )

    is_paid = django_filters.BooleanFilter(
        method='filter_is_paid',
        label='Is Fully Paid'
    )

    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue',
        label='Is Overdue'
    )

    # Date filters
    issue_date_after = django_filters.DateFilter(
        field_name='issue_date',
        lookup_expr='gte',
        label='Issue Date After'
    )

    issue_date_before = django_filters.DateFilter(
        field_name='issue_date',
        lookup_expr='lte',
        label='Issue Date Before'
    )

    due_date_after = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='gte',
        label='Due Date After'
    )

    due_date_before = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='lte',
        label='Due Date Before'
    )

    class Meta:
        model = Invoice
        fields = [
            'status',
            'client',
            'contract',
        ]

    def filter_is_paid(self, queryset, name, value):
        """Filter fully paid invoices."""
        if value:
            return queryset.filter(status=Invoice.PAID)
        else:
            return queryset.exclude(status=Invoice.PAID)

    def filter_is_overdue(self, queryset, name, value):
        """Filter overdue invoices."""
        from django.utils import timezone
        today = timezone.now().date()

        if value:
            return queryset.filter(
                due_date__lt=today
            ).exclude(
                status__in=[Invoice.PAID, Invoice.CANCELLED]
            )
        else:
            return queryset.filter(
                Q(due_date__gte=today) | Q(status__in=[Invoice.PAID, Invoice.CANCELLED])
            )
