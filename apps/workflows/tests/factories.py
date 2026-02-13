"""
Factory Boy factories for the workflows app.
"""

import factory
from django.utils import timezone
from apps.accounts.models import User
from apps.workflows.models import (
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowActionExecution,
)


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'wfuser{n}@test.com')
    username = factory.Sequence(lambda n: f'wfuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    role = User.ADMIN


class WorkflowFactory(factory.django.DjangoModelFactory):
    """Factory for creating Workflow instances."""

    class Meta:
        model = Workflow

    name = factory.Sequence(lambda n: f'Workflow {n}')
    description = factory.Faker('sentence')
    is_active = True
    trigger_type = Workflow.CONTRACT_SIGNED
    trigger_config = factory.LazyFunction(dict)
    owner = factory.SubFactory(UserFactory)


class WorkflowActionFactory(factory.django.DjangoModelFactory):
    """Factory for creating WorkflowAction instances."""

    class Meta:
        model = WorkflowAction

    workflow = factory.SubFactory(WorkflowFactory)
    action_type = WorkflowAction.SEND_EMAIL
    action_config = factory.LazyFunction(lambda: {'to': 'user@example.com', 'subject': 'Test'})
    order = factory.Sequence(lambda n: n)
    delay_minutes = 0
    is_active = True


class WorkflowExecutionFactory(factory.django.DjangoModelFactory):
    """Factory for creating WorkflowExecution instances."""

    class Meta:
        model = WorkflowExecution

    workflow = factory.SubFactory(WorkflowFactory)
    status = WorkflowExecution.PENDING
    triggered_by = factory.SubFactory(UserFactory)
    trigger_data = factory.LazyFunction(dict)
    started_at = None
    completed_at = None
    error_message = ''


class WorkflowActionExecutionFactory(factory.django.DjangoModelFactory):
    """Factory for creating WorkflowActionExecution instances."""

    class Meta:
        model = WorkflowActionExecution

    execution = factory.SubFactory(WorkflowExecutionFactory)
    action = factory.SubFactory(WorkflowActionFactory)
    status = WorkflowActionExecution.PENDING
    result_data = factory.LazyFunction(dict)
    started_at = None
    completed_at = None
    error_message = ''
