"""
Factory Boy factories for the tasks app.
"""

import factory
from django.utils import timezone
from apps.accounts.models import User
from apps.tasks.models import Task, TaskComment


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f'taskuser{n}@test.com')
    username = factory.Sequence(lambda n: f'taskuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda o: f'{o.first_name} {o.last_name}')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    role = User.ADMIN


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating Task instances."""

    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f'Task {n}')
    description = factory.Faker('sentence')
    status = Task.TODO
    priority = Task.MEDIUM
    due_date = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7))
    assigned_to = factory.SubFactory(UserFactory)
    created_by = factory.SubFactory(UserFactory)
    client = None
    contract = None
    invoice = None
    tags = factory.LazyFunction(list)
    completed_at = None


class TaskCommentFactory(factory.django.DjangoModelFactory):
    """Factory for creating TaskComment instances."""

    class Meta:
        model = TaskComment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph')
