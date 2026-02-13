"""
Filters for the tasks app.
"""

import django_filters
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """
    Filter class for Task model.
    """

    # Status filter
    status = django_filters.MultipleChoiceFilter(
        choices=Task.STATUS_CHOICES,
        label='Status'
    )

    # Priority filter
    priority = django_filters.MultipleChoiceFilter(
        choices=Task.PRIORITY_CHOICES,
        label='Priority'
    )

    # Assigned to filter
    assigned_to = django_filters.UUIDFilter(
        field_name='assigned_to__id',
        label='Assigned To (User ID)'
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

    # Due date range filters
    due_date_after = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte',
        label='Due Date After'
    )

    due_date_before = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte',
        label='Due Date Before'
    )

    class Meta:
        model = Task
        fields = [
            'status',
            'priority',
            'assigned_to',
            'client',
            'contract',
        ]
