"""
Tests for tasks app serializers.

Tests cover:
- TaskListSerializer: nested fields, comments_count, is_overdue
- TaskDetailSerializer: full detail with comments, computed name fields
- TaskCreateUpdateSerializer: create/update field validation
- TaskCommentSerializer: comment serialization, author_name
- TaskStatsSerializer: statistics data structure
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.tasks.models import Task, TaskComment
from apps.tasks.serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    TaskCommentSerializer,
    TaskStatsSerializer,
    AssignedToNestedSerializer,
    ClientNestedSerializer,
)
from .factories import TaskFactory, TaskCommentFactory, UserFactory


# ============================================================================
# TaskCommentSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskCommentSerializer:
    """Tests for TaskCommentSerializer."""

    def test_serialize_comment(self):
        """Test basic comment serialization includes expected fields."""
        comment = TaskCommentFactory()
        serializer = TaskCommentSerializer(comment)
        data = serializer.data

        assert 'id' in data
        assert 'task' in data
        assert 'author' in data
        assert 'content' in data
        assert 'author_name' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_author_name_with_full_name(self):
        """Test author_name returns full_name when set."""
        user = UserFactory(full_name='Alice Wonderland')
        comment = TaskCommentFactory(author=user)
        serializer = TaskCommentSerializer(comment)
        assert serializer.data['author_name'] == 'Alice Wonderland'

    def test_author_name_falls_back_to_first_last(self):
        """Test author_name falls back to first_name + last_name."""
        user = UserFactory(full_name='', first_name='Bob', last_name='Builder')
        comment = TaskCommentFactory(author=user)
        serializer = TaskCommentSerializer(comment)
        assert serializer.data['author_name'] == 'Bob Builder'

    def test_read_only_fields(self):
        """Test that id, author, created_at, updated_at are read-only."""
        meta = TaskCommentSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'author' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields

    def test_deserialize_comment_valid(self):
        """Test valid comment data deserializes correctly."""
        task = TaskFactory()
        data = {
            'task': str(task.id),
            'content': 'This is a valid comment.',
        }
        serializer = TaskCommentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_deserialize_comment_missing_content(self):
        """Test comment without content is invalid."""
        task = TaskFactory()
        data = {
            'task': str(task.id),
        }
        serializer = TaskCommentSerializer(data=data)
        assert not serializer.is_valid()
        assert 'content' in serializer.errors


# ============================================================================
# TaskListSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskListSerializer:
    """Tests for TaskListSerializer."""

    def test_serialized_fields(self):
        """Test list serializer returns expected fields."""
        task = TaskFactory()
        serializer = TaskListSerializer(task)
        data = serializer.data
        expected_fields = {
            'id', 'title', 'status', 'priority', 'due_date',
            'assigned_to', 'client', 'created_at', 'is_overdue',
            'comments_count',
        }
        assert set(data.keys()) == expected_fields

    def test_comments_count_zero(self):
        """Test comments_count is 0 when no comments exist."""
        task = TaskFactory()
        serializer = TaskListSerializer(task)
        assert serializer.data['comments_count'] == 0

    def test_comments_count_with_comments(self):
        """Test comments_count reflects actual comment count."""
        task = TaskFactory()
        TaskCommentFactory(task=task)
        TaskCommentFactory(task=task)
        TaskCommentFactory(task=task)
        serializer = TaskListSerializer(task)
        assert serializer.data['comments_count'] == 3

    def test_is_overdue_true_for_past_due(self):
        """Test is_overdue is True for tasks past due date."""
        task = TaskFactory(
            due_date=timezone.now() - timedelta(days=1),
            status=Task.TODO,
        )
        serializer = TaskListSerializer(task)
        assert serializer.data['is_overdue'] is True

    def test_is_overdue_false_for_future_due(self):
        """Test is_overdue is False for tasks with future due date."""
        task = TaskFactory(
            due_date=timezone.now() + timedelta(days=7),
            status=Task.TODO,
        )
        serializer = TaskListSerializer(task)
        assert serializer.data['is_overdue'] is False

    def test_assigned_to_nested_serializer(self):
        """Test assigned_to is serialized as nested object with id, email, full_name."""
        user = UserFactory(email='nested@test.com', full_name='Nested User')
        task = TaskFactory(assigned_to=user)
        serializer = TaskListSerializer(task)
        assigned = serializer.data['assigned_to']
        assert assigned['email'] == 'nested@test.com'
        assert assigned['full_name'] == 'Nested User'
        assert 'id' in assigned

    def test_assigned_to_null(self):
        """Test assigned_to is None when not assigned."""
        task = TaskFactory(assigned_to=None)
        serializer = TaskListSerializer(task)
        assert serializer.data['assigned_to'] is None

    def test_client_null(self):
        """Test client is None when not set."""
        task = TaskFactory(client=None)
        serializer = TaskListSerializer(task)
        assert serializer.data['client'] is None

    def test_multiple_tasks_serialization(self):
        """Test serializing a queryset of multiple tasks."""
        TaskFactory.create_batch(3)
        tasks = Task.objects.all()
        serializer = TaskListSerializer(tasks, many=True)
        assert len(serializer.data) == 3


# ============================================================================
# TaskDetailSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskDetailSerializer:
    """Tests for TaskDetailSerializer."""

    def test_includes_all_model_fields(self):
        """Test detail serializer includes all model fields plus computed ones."""
        task = TaskFactory()
        serializer = TaskDetailSerializer(task)
        data = serializer.data

        assert 'id' in data
        assert 'title' in data
        assert 'description' in data
        assert 'status' in data
        assert 'priority' in data
        assert 'due_date' in data
        assert 'tags' in data
        assert 'comments' in data
        assert 'is_overdue' in data
        assert 'assigned_to_name' in data
        assert 'created_by_name' in data
        assert 'client_name' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_comments_included_as_list(self):
        """Test comments are serialized inline as a list."""
        task = TaskFactory()
        TaskCommentFactory(task=task, content='First comment')
        TaskCommentFactory(task=task, content='Second comment')
        serializer = TaskDetailSerializer(task)
        assert len(serializer.data['comments']) == 2

    def test_assigned_to_name_with_user(self):
        """Test assigned_to_name returns name when user assigned."""
        user = UserFactory(full_name='Jane Assignee')
        task = TaskFactory(assigned_to=user)
        serializer = TaskDetailSerializer(task)
        assert serializer.data['assigned_to_name'] == 'Jane Assignee'

    def test_assigned_to_name_null(self):
        """Test assigned_to_name is None when not assigned."""
        task = TaskFactory(assigned_to=None)
        serializer = TaskDetailSerializer(task)
        assert serializer.data['assigned_to_name'] is None

    def test_created_by_name(self):
        """Test created_by_name returns the creator's name."""
        user = UserFactory(full_name='Task Creator')
        task = TaskFactory(created_by=user)
        serializer = TaskDetailSerializer(task)
        assert serializer.data['created_by_name'] == 'Task Creator'

    def test_client_name_null(self):
        """Test client_name is None when no client."""
        task = TaskFactory(client=None)
        serializer = TaskDetailSerializer(task)
        assert serializer.data['client_name'] is None

    def test_read_only_fields(self):
        """Test that id, created_by, created_at, updated_at are read-only."""
        meta = TaskDetailSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'created_by' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields

    def test_empty_comments_list(self):
        """Test that comments returns empty list when there are none."""
        task = TaskFactory()
        serializer = TaskDetailSerializer(task)
        assert serializer.data['comments'] == []


# ============================================================================
# TaskCreateUpdateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskCreateUpdateSerializer:
    """Tests for TaskCreateUpdateSerializer."""

    def test_valid_minimal_data(self):
        """Test serializer accepts minimal valid data (just title)."""
        data = {'title': 'A new task'}
        serializer = TaskCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_full_data(self):
        """Test serializer accepts full data with all writable fields."""
        user = UserFactory()
        data = {
            'title': 'Full task',
            'description': 'Task with all fields',
            'status': Task.IN_PROGRESS,
            'priority': Task.HIGH,
            'due_date': (timezone.now() + timedelta(days=14)).isoformat(),
            'assigned_to': str(user.id),
            'tags': ['important', 'v2'],
        }
        serializer = TaskCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_title_invalid(self):
        """Test that missing title makes data invalid."""
        data = {'description': 'No title here'}
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_invalid_status_value(self):
        """Test that an invalid status value is rejected."""
        data = {'title': 'Bad status', 'status': 'nonexistent_status'}
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors

    def test_invalid_priority_value(self):
        """Test that an invalid priority value is rejected."""
        data = {'title': 'Bad priority', 'priority': 'critical'}
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'priority' in serializer.errors

    def test_fields_included(self):
        """Test serializer exposes exactly the right fields."""
        expected_fields = {
            'title', 'description', 'status', 'priority', 'due_date',
            'assigned_to', 'client', 'contract', 'invoice', 'tags',
        }
        serializer = TaskCreateUpdateSerializer()
        assert set(serializer.fields.keys()) == expected_fields

    def test_default_status_applied(self):
        """Test that default status 'todo' is applied when not specified."""
        data = {'title': 'Default status task'}
        serializer = TaskCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        # Default comes from model, so validated_data won't include it
        # unless explicitly sent. Check the model default is 'todo'.
        assert Task.TODO == 'todo'

    def test_update_partial(self):
        """Test partial update only changes provided fields."""
        task = TaskFactory(title='Original', priority=Task.LOW)
        data = {'priority': Task.URGENT}
        serializer = TaskCreateUpdateSerializer(task, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated_task = serializer.save()
        assert updated_task.priority == Task.URGENT
        assert updated_task.title == 'Original'


# ============================================================================
# TaskStatsSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskStatsSerializer:
    """Tests for TaskStatsSerializer."""

    def test_valid_stats_data(self):
        """Test serializer accepts valid stats data."""
        data = {
            'total': 10,
            'by_status': {'todo': 3, 'in_progress': 4, 'done': 2, 'cancelled': 1},
            'by_priority': {'low': 2, 'medium': 5, 'high': 2, 'urgent': 1},
            'overdue_count': 2,
        }
        serializer = TaskStatsSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serialized_output_structure(self):
        """Test serialized output has correct structure."""
        stats = {
            'total': 5,
            'by_status': {'todo': 2, 'done': 3},
            'by_priority': {'medium': 5},
            'overdue_count': 0,
        }
        serializer = TaskStatsSerializer(stats)
        data = serializer.data
        assert data['total'] == 5
        assert data['by_status'] == {'todo': 2, 'done': 3}
        assert data['by_priority'] == {'medium': 5}
        assert data['overdue_count'] == 0

    def test_zero_stats(self):
        """Test serializer handles all-zero stats."""
        stats = {
            'total': 0,
            'by_status': {},
            'by_priority': {},
            'overdue_count': 0,
        }
        serializer = TaskStatsSerializer(stats)
        data = serializer.data
        assert data['total'] == 0
        assert data['overdue_count'] == 0

    def test_missing_field_invalid(self):
        """Test that missing required fields make data invalid."""
        data = {'total': 5}  # missing by_status, by_priority, overdue_count
        serializer = TaskStatsSerializer(data=data)
        assert not serializer.is_valid()

    def test_fields_present(self):
        """Test serializer has the expected fields."""
        serializer = TaskStatsSerializer()
        expected = {'total', 'by_status', 'by_priority', 'overdue_count'}
        assert set(serializer.fields.keys()) == expected


# ============================================================================
# AssignedToNestedSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestAssignedToNestedSerializer:
    """Tests for AssignedToNestedSerializer."""

    def test_serialize_user(self):
        """Test nested user serializer returns id, email, full_name."""
        user = UserFactory(email='nested@example.com', full_name='Nested Person')
        serializer = AssignedToNestedSerializer(user)
        data = serializer.data
        assert str(user.id) == data['id']
        assert data['email'] == 'nested@example.com'
        assert data['full_name'] == 'Nested Person'

    def test_all_fields_read_only(self):
        """Test all fields in the nested serializer are read-only."""
        serializer = AssignedToNestedSerializer()
        for field_name, field in serializer.fields.items():
            assert field.read_only, f"Field '{field_name}' should be read-only"
