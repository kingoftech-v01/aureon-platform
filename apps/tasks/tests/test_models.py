"""
Tests for tasks app models.

Tests cover:
- Task creation, __str__, is_overdue property, status choices
- TaskComment creation, __str__, relationships
"""

import uuid
import pytest
from datetime import timedelta
from django.utils import timezone

from apps.tasks.models import Task, TaskComment
from .factories import TaskFactory, TaskCommentFactory, UserFactory


# ============================================================================
# Task Model Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskModel:
    """Tests for the Task model."""

    def test_create_task(self):
        """Test creating a task with all fields."""
        user = UserFactory()
        task = TaskFactory(
            title='Test Task',
            description='A test task',
            status=Task.TODO,
            priority=Task.HIGH,
            created_by=user,
            assigned_to=user,
            tags=['urgent', 'feature'],
        )

        assert task.title == 'Test Task'
        assert task.description == 'A test task'
        assert task.status == Task.TODO
        assert task.priority == Task.HIGH
        assert task.created_by == user
        assert task.assigned_to == user
        assert task.tags == ['urgent', 'feature']

    def test_task_str(self):
        """Test task string representation."""
        task = TaskFactory(title='My Important Task')
        assert str(task) == 'My Important Task'

    def test_task_uuid_primary_key(self):
        """Test task has UUID primary key."""
        task = TaskFactory()
        assert isinstance(task.id, uuid.UUID)

    def test_task_default_status(self):
        """Test task defaults to TODO status."""
        task = TaskFactory()
        assert task.status == Task.TODO

    def test_task_default_priority(self):
        """Test task defaults to MEDIUM priority."""
        task = TaskFactory()
        assert task.priority == Task.MEDIUM

    def test_task_timestamps(self):
        """Test task has created_at and updated_at timestamps."""
        task = TaskFactory()
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_ordering(self):
        """Test tasks are ordered by -created_at."""
        t1 = TaskFactory()
        t2 = TaskFactory()
        tasks = list(Task.objects.all())
        assert tasks[0].created_at >= tasks[1].created_at

    def test_task_status_choices(self):
        """Test all status choices are valid."""
        valid_statuses = [Task.TODO, Task.IN_PROGRESS, Task.DONE, Task.CANCELLED]
        choices_dict = dict(Task.STATUS_CHOICES)
        for status_val in valid_statuses:
            assert status_val in choices_dict

    def test_task_priority_choices(self):
        """Test all priority choices are valid."""
        valid_priorities = [Task.LOW, Task.MEDIUM, Task.HIGH, Task.URGENT]
        choices_dict = dict(Task.PRIORITY_CHOICES)
        for priority_val in valid_priorities:
            assert priority_val in choices_dict

    def test_task_assigned_to_nullable(self):
        """Test task can have no assigned_to."""
        task = TaskFactory(assigned_to=None)
        assert task.assigned_to is None

    def test_task_client_nullable(self):
        """Test task can have no client."""
        task = TaskFactory(client=None)
        assert task.client is None

    def test_task_contract_nullable(self):
        """Test task can have no contract."""
        task = TaskFactory(contract=None)
        assert task.contract is None

    def test_task_invoice_nullable(self):
        """Test task can have no invoice."""
        task = TaskFactory(invoice=None)
        assert task.invoice is None

    def test_task_due_date_nullable(self):
        """Test task can have no due date."""
        task = TaskFactory(due_date=None)
        assert task.due_date is None

    def test_task_completed_at_nullable(self):
        """Test completed_at is null by default."""
        task = TaskFactory()
        assert task.completed_at is None

    def test_task_tags_default_empty_list(self):
        """Test tags defaults to empty list."""
        task = TaskFactory(tags=[])
        assert task.tags == []

    def test_task_description_blank(self):
        """Test task can have blank description."""
        task = TaskFactory(description='')
        assert task.description == ''

    def test_task_comments_relationship(self):
        """Test task can have related comments."""
        task = TaskFactory()
        TaskCommentFactory(task=task)
        TaskCommentFactory(task=task)
        assert task.comments.count() == 2


# ============================================================================
# Task is_overdue Property Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskIsOverdue:
    """Tests for the Task is_overdue property."""

    def test_is_overdue_past_due_date(self):
        """Test is_overdue returns True for past due date."""
        task = TaskFactory(
            due_date=timezone.now() - timedelta(days=1),
            status=Task.TODO,
        )
        assert task.is_overdue is True

    def test_is_overdue_future_due_date(self):
        """Test is_overdue returns False for future due date."""
        task = TaskFactory(
            due_date=timezone.now() + timedelta(days=1),
            status=Task.TODO,
        )
        assert task.is_overdue is False

    def test_is_overdue_no_due_date(self):
        """Test is_overdue returns False when no due date."""
        task = TaskFactory(due_date=None, status=Task.TODO)
        assert task.is_overdue is False

    def test_is_overdue_done_status(self):
        """Test is_overdue returns False when task is done."""
        task = TaskFactory(
            due_date=timezone.now() - timedelta(days=1),
            status=Task.DONE,
        )
        assert task.is_overdue is False

    def test_is_overdue_cancelled_status(self):
        """Test is_overdue returns False when task is cancelled."""
        task = TaskFactory(
            due_date=timezone.now() - timedelta(days=1),
            status=Task.CANCELLED,
        )
        assert task.is_overdue is False

    def test_is_overdue_in_progress_past_due(self):
        """Test is_overdue returns True for in_progress tasks past due."""
        task = TaskFactory(
            due_date=timezone.now() - timedelta(days=1),
            status=Task.IN_PROGRESS,
        )
        assert task.is_overdue is True

    def test_is_overdue_in_progress_not_due(self):
        """Test is_overdue returns False for in_progress tasks not yet due."""
        task = TaskFactory(
            due_date=timezone.now() + timedelta(days=1),
            status=Task.IN_PROGRESS,
        )
        assert task.is_overdue is False


# ============================================================================
# Task Status Transition Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskStatusTransitions:
    """Tests for task status transitions."""

    def test_transition_to_in_progress(self):
        """Test transitioning task to IN_PROGRESS."""
        task = TaskFactory(status=Task.TODO)
        task.status = Task.IN_PROGRESS
        task.save()
        task.refresh_from_db()
        assert task.status == Task.IN_PROGRESS

    def test_transition_to_done(self):
        """Test transitioning task to DONE."""
        task = TaskFactory(status=Task.IN_PROGRESS)
        task.status = Task.DONE
        task.completed_at = timezone.now()
        task.save()
        task.refresh_from_db()
        assert task.status == Task.DONE
        assert task.completed_at is not None

    def test_transition_to_cancelled(self):
        """Test transitioning task to CANCELLED."""
        task = TaskFactory(status=Task.TODO)
        task.status = Task.CANCELLED
        task.save()
        task.refresh_from_db()
        assert task.status == Task.CANCELLED

    def test_reopen_done_task(self):
        """Test reopening a done task."""
        task = TaskFactory(status=Task.DONE, completed_at=timezone.now())
        task.status = Task.TODO
        task.completed_at = None
        task.save()
        task.refresh_from_db()
        assert task.status == Task.TODO
        assert task.completed_at is None


# ============================================================================
# TaskComment Model Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskCommentModel:
    """Tests for the TaskComment model."""

    def test_create_task_comment(self):
        """Test creating a task comment."""
        user = UserFactory()
        task = TaskFactory(created_by=user)
        comment = TaskCommentFactory(
            task=task,
            author=user,
            content='This is a test comment',
        )

        assert comment.task == task
        assert comment.author == user
        assert comment.content == 'This is a test comment'

    def test_task_comment_str(self):
        """Test task comment string representation."""
        user = UserFactory(first_name='John', last_name='Doe')
        task = TaskFactory(title='My Task', created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        expected = f"Comment on My Task by {user}"
        assert str(comment) == expected

    def test_task_comment_uuid_primary_key(self):
        """Test comment has UUID primary key."""
        comment = TaskCommentFactory()
        assert isinstance(comment.id, uuid.UUID)

    def test_task_comment_timestamps(self):
        """Test comment has timestamps."""
        comment = TaskCommentFactory()
        assert comment.created_at is not None
        assert comment.updated_at is not None

    def test_task_comment_ordering(self):
        """Test comments are ordered by created_at."""
        task = TaskFactory()
        c1 = TaskCommentFactory(task=task)
        c2 = TaskCommentFactory(task=task)
        comments = list(task.comments.all())
        assert comments[0].created_at <= comments[1].created_at

    def test_task_comment_cascade_delete(self):
        """Test comments are deleted when task is deleted."""
        task = TaskFactory()
        TaskCommentFactory(task=task)
        TaskCommentFactory(task=task)
        assert TaskComment.objects.filter(task=task).count() == 2

        task.delete()
        assert TaskComment.objects.filter(task=task).count() == 0
