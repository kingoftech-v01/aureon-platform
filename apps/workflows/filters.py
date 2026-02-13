"""
Filters for the workflows app.
"""

import django_filters
from .models import Workflow


class WorkflowFilter(django_filters.FilterSet):
    """
    Filter class for Workflow model.
    """

    # Trigger type filter
    trigger_type = django_filters.ChoiceFilter(
        choices=Workflow.TRIGGER_TYPE_CHOICES,
        label='Trigger Type'
    )

    # Active filter
    is_active = django_filters.BooleanFilter(
        label='Is Active'
    )

    # Owner filter
    owner = django_filters.UUIDFilter(
        field_name='owner__id',
        label='Owner ID'
    )

    class Meta:
        model = Workflow
        fields = [
            'trigger_type',
            'is_active',
            'owner',
        ]
