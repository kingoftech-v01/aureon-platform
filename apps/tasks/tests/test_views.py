"""
Tests for tasks app API views.

Tests cover:
- TaskViewSet: list, retrieve, create, update, partial_update, destroy
- TaskViewSet custom actions: complete, reopen, stats, comments
- TaskCommentViewSet: list, create, update, destroy
- Authentication and permission checks
- Filtering and search
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.tasks.models import Task, TaskComment
from .factories import TaskFactory, TaskCommentFactory, UserFactory


# ============================================================================
# Helpers
# ============================================================================

# The URL structure is: root 'api/tasks/' + app 'api/' + router 'tasks/'
TASKS_API_URL = '/api/tasks/api/tasks/'
TASK_COMMENTS_API_URL = '/api/tasks/api/task-comments/'


def task_detail_url(task_id):
    return f'{TASKS_API_URL}{task_id}/'


def task_action_url(task_id, action):
    return f'{TASKS_API_URL}{task_id}/{action}/'


def comment_detail_url(comment_id):
    return f'{TASK_COMMENTS_API_URL}{comment_id}/'


# ============================================================================
# TaskViewSet - Authentication Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetAuthentication:
    """Tests for authentication requirements on TaskViewSet."""

    def test_list_requires_authentication(self, api_client):
        """Test that unauthenticated users cannot list tasks."""
        response = api_client.get(TASKS_API_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_create_requires_authentication(self, api_client):
        """Test that unauthenticated users cannot create tasks."""
        data = {'title': 'Unauthorized task'}
        response = api_client.post(TASKS_API_URL, data)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_retrieve_requires_authentication(self, api_client):
        """Test that unauthenticated users cannot retrieve a task."""
        task = TaskFactory()
        response = api_client.get(task_detail_url(task.id))
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ============================================================================
# TaskViewSet - List Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetList:
    """Tests for TaskViewSet list action."""

    def test_list_tasks_empty(self, authenticated_admin_client):
        """Test listing tasks returns empty list when no tasks exist."""
        response = authenticated_admin_client.get(TASKS_API_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 0

    def test_list_tasks_returns_tasks(self, authenticated_admin_client):
        """Test listing tasks returns all tasks."""
        TaskFactory.create_batch(3)
        response = authenticated_admin_client.get(TASKS_API_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 3

    def test_list_tasks_uses_list_serializer(self, authenticated_admin_client):
        """Test list action returns fields from TaskListSerializer."""
        TaskFactory()
        response = authenticated_admin_client.get(TASKS_API_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        task_data = results[0]
        # TaskListSerializer fields
        assert 'title' in task_data
        assert 'comments_count' in task_data
        assert 'is_overdue' in task_data
        # Should NOT include detail-only fields like 'description' or 'comments'
        assert 'comments' not in task_data

    def test_list_search_by_title(self, authenticated_admin_client):
        """Test searching tasks by title."""
        TaskFactory(title='Deploy to production')
        TaskFactory(title='Fix login bug')
        response = authenticated_admin_client.get(TASKS_API_URL, {'search': 'Deploy'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['title'] == 'Deploy to production'

    def test_list_filter_by_status(self, authenticated_admin_client):
        """Test filtering tasks by status."""
        TaskFactory(status=Task.TODO)
        TaskFactory(status=Task.DONE)
        TaskFactory(status=Task.DONE)
        response = authenticated_admin_client.get(TASKS_API_URL, {'status': Task.DONE})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 2

    def test_list_filter_by_priority(self, authenticated_admin_client):
        """Test filtering tasks by priority."""
        TaskFactory(priority=Task.URGENT)
        TaskFactory(priority=Task.LOW)
        response = authenticated_admin_client.get(TASKS_API_URL, {'priority': Task.URGENT})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['priority'] == Task.URGENT


# ============================================================================
# TaskViewSet - Retrieve Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetRetrieve:
    """Tests for TaskViewSet retrieve action."""

    def test_retrieve_task(self, authenticated_admin_client):
        """Test retrieving a single task returns detail serializer data."""
        task = TaskFactory(title='Specific task')
        response = authenticated_admin_client.get(task_detail_url(task.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Specific task'
        # Detail serializer includes comments and description
        assert 'comments' in response.data
        assert 'description' in response.data
        assert 'assigned_to_name' in response.data
        assert 'created_by_name' in response.data

    def test_retrieve_nonexistent_task(self, authenticated_admin_client):
        """Test retrieving a non-existent task returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        response = authenticated_admin_client.get(task_detail_url(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_includes_comments(self, authenticated_admin_client):
        """Test retrieved task includes inline comments."""
        task = TaskFactory()
        TaskCommentFactory(task=task, content='Inline comment')
        response = authenticated_admin_client.get(task_detail_url(task.id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['comments']) == 1
        assert response.data['comments'][0]['content'] == 'Inline comment'


# ============================================================================
# TaskViewSet - Create Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetCreate:
    """Tests for TaskViewSet create action."""

    def test_create_task_minimal(self, authenticated_admin_client):
        """Test creating a task with only title."""
        data = {'title': 'New task from API'}
        response = authenticated_admin_client.post(TASKS_API_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Task.objects.filter(title='New task from API').exists()

    def test_create_task_sets_created_by(self, authenticated_admin_client, admin_user):
        """Test that created_by is set to the authenticated user."""
        data = {'title': 'Task with creator'}
        response = authenticated_admin_client.post(TASKS_API_URL, data)
        assert response.status_code == status.HTTP_201_CREATED
        task = Task.objects.get(title='Task with creator')
        assert task.created_by == admin_user

    def test_create_task_with_all_fields(self, authenticated_admin_client):
        """Test creating a task with all writable fields."""
        user = UserFactory()
        data = {
            'title': 'Full task',
            'description': 'A complete task',
            'status': Task.IN_PROGRESS,
            'priority': Task.HIGH,
            'due_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'assigned_to': str(user.id),
            'tags': ['api', 'test'],
        }
        response = authenticated_admin_client.post(
            TASKS_API_URL, data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        task = Task.objects.get(title='Full task')
        assert task.priority == Task.HIGH
        assert task.assigned_to == user
        assert task.tags == ['api', 'test']

    def test_create_task_invalid_data(self, authenticated_admin_client):
        """Test creating a task without title returns 400."""
        data = {'description': 'Missing title'}
        response = authenticated_admin_client.post(TASKS_API_URL, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TaskViewSet - Update Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetUpdate:
    """Tests for TaskViewSet update and partial_update actions."""

    def test_full_update_task(self, authenticated_admin_client):
        """Test full update (PUT) of a task."""
        task = TaskFactory(title='Original title')
        data = {
            'title': 'Updated title',
            'description': 'Updated description',
            'status': Task.IN_PROGRESS,
            'priority': Task.URGENT,
        }
        response = authenticated_admin_client.put(
            task_detail_url(task.id), data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == 'Updated title'
        assert task.status == Task.IN_PROGRESS

    def test_partial_update_task(self, authenticated_admin_client):
        """Test partial update (PATCH) of a task."""
        task = TaskFactory(title='Keep this', priority=Task.LOW)
        data = {'priority': Task.HIGH}
        response = authenticated_admin_client.patch(
            task_detail_url(task.id), data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.priority == Task.HIGH
        assert task.title == 'Keep this'


# ============================================================================
# TaskViewSet - Delete Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetDelete:
    """Tests for TaskViewSet destroy action."""

    def test_delete_task(self, authenticated_admin_client):
        """Test deleting a task."""
        task = TaskFactory()
        task_id = task.id
        response = authenticated_admin_client.delete(task_detail_url(task_id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task_id).exists()

    def test_delete_nonexistent_task(self, authenticated_admin_client):
        """Test deleting a non-existent task returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        response = authenticated_admin_client.delete(task_detail_url(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TaskViewSet - Complete Action Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetComplete:
    """Tests for the 'complete' custom action."""

    def test_complete_task(self, authenticated_admin_client):
        """Test completing a task sets status to DONE and completed_at."""
        task = TaskFactory(status=Task.IN_PROGRESS)
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'complete')
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.DONE
        assert task.completed_at is not None

    def test_complete_already_done_task(self, authenticated_admin_client):
        """Test completing an already-done task returns 400."""
        task = TaskFactory(status=Task.DONE, completed_at=timezone.now())
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'complete')
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already completed' in response.data['detail'].lower()

    def test_complete_todo_task(self, authenticated_admin_client):
        """Test completing a TODO task works."""
        task = TaskFactory(status=Task.TODO)
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'complete')
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.DONE

    def test_complete_returns_detail_serializer(self, authenticated_admin_client):
        """Test that complete action returns full detail data."""
        task = TaskFactory(status=Task.TODO)
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'complete')
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'comments' in response.data
        assert 'assigned_to_name' in response.data


# ============================================================================
# TaskViewSet - Reopen Action Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetReopen:
    """Tests for the 'reopen' custom action."""

    def test_reopen_done_task(self, authenticated_admin_client):
        """Test reopening a done task sets status to TODO and clears completed_at."""
        task = TaskFactory(status=Task.DONE, completed_at=timezone.now())
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'reopen')
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.TODO
        assert task.completed_at is None

    def test_reopen_cancelled_task(self, authenticated_admin_client):
        """Test reopening a cancelled task sets it back to TODO."""
        task = TaskFactory(status=Task.CANCELLED)
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'reopen')
        )
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.TODO

    def test_reopen_returns_detail_serializer(self, authenticated_admin_client):
        """Test that reopen action returns full detail data."""
        task = TaskFactory(status=Task.DONE, completed_at=timezone.now())
        response = authenticated_admin_client.post(
            task_action_url(task.id, 'reopen')
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'comments' in response.data


# ============================================================================
# TaskViewSet - Stats Action Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetStats:
    """Tests for the 'stats' custom action."""

    def test_stats_empty(self, authenticated_admin_client):
        """Test stats when no tasks exist."""
        response = authenticated_admin_client.get(f'{TASKS_API_URL}stats/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 0
        assert response.data['overdue_count'] == 0

    def test_stats_with_tasks(self, authenticated_admin_client):
        """Test stats returns correct counts."""
        TaskFactory(status=Task.TODO, priority=Task.HIGH)
        TaskFactory(status=Task.TODO, priority=Task.LOW)
        TaskFactory(status=Task.DONE, priority=Task.MEDIUM)
        TaskFactory(status=Task.IN_PROGRESS, priority=Task.MEDIUM)

        response = authenticated_admin_client.get(f'{TASKS_API_URL}stats/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 4
        assert response.data['by_status']['todo'] == 2
        assert response.data['by_status']['done'] == 1
        assert response.data['by_status']['in_progress'] == 1
        assert response.data['by_priority']['medium'] == 2

    def test_stats_overdue_count(self, authenticated_admin_client):
        """Test stats correctly counts overdue tasks."""
        # Overdue: not done/cancelled and due_date in the past
        TaskFactory(
            status=Task.TODO,
            due_date=timezone.now() - timedelta(days=1),
        )
        TaskFactory(
            status=Task.IN_PROGRESS,
            due_date=timezone.now() - timedelta(days=3),
        )
        # Not overdue: done with past due date
        TaskFactory(
            status=Task.DONE,
            due_date=timezone.now() - timedelta(days=1),
        )
        # Not overdue: future due date
        TaskFactory(
            status=Task.TODO,
            due_date=timezone.now() + timedelta(days=5),
        )

        response = authenticated_admin_client.get(f'{TASKS_API_URL}stats/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['overdue_count'] == 2

    def test_stats_structure(self, authenticated_admin_client):
        """Test stats response has expected structure."""
        response = authenticated_admin_client.get(f'{TASKS_API_URL}stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert 'by_status' in response.data
        assert 'by_priority' in response.data
        assert 'overdue_count' in response.data


# ============================================================================
# TaskViewSet - Comments Action Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskViewSetComments:
    """Tests for the 'comments' custom action on a task."""

    def test_get_comments_for_task(self, authenticated_admin_client):
        """Test retrieving comments for a specific task."""
        task = TaskFactory()
        TaskCommentFactory(task=task, content='Comment A')
        TaskCommentFactory(task=task, content='Comment B')
        # Comment on a different task (should not appear)
        TaskCommentFactory(content='Other task comment')

        response = authenticated_admin_client.get(
            task_action_url(task.id, 'comments')
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_get_comments_empty(self, authenticated_admin_client):
        """Test retrieving comments returns empty list when none exist."""
        task = TaskFactory()
        response = authenticated_admin_client.get(
            task_action_url(task.id, 'comments')
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


# ============================================================================
# TaskCommentViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskCommentViewSet:
    """Tests for TaskCommentViewSet."""

    def test_list_comments(self, authenticated_admin_client):
        """Test listing all comments."""
        TaskCommentFactory.create_batch(3)
        response = authenticated_admin_client.get(TASK_COMMENTS_API_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 3

    def test_create_comment(self, authenticated_admin_client, admin_user):
        """Test creating a comment sets author to current user."""
        task = TaskFactory()
        data = {
            'task': str(task.id),
            'content': 'New comment via API',
        }
        response = authenticated_admin_client.post(
            TASK_COMMENTS_API_URL, data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        comment = TaskComment.objects.get(content='New comment via API')
        assert comment.author == admin_user
        assert comment.task == task

    def test_create_comment_missing_content(self, authenticated_admin_client):
        """Test creating a comment without content returns 400."""
        task = TaskFactory()
        data = {'task': str(task.id)}
        response = authenticated_admin_client.post(
            TASK_COMMENTS_API_URL, data, format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_comment(self, authenticated_admin_client, admin_user):
        """Test updating a comment."""
        comment = TaskCommentFactory(author=admin_user, content='Original')
        data = {
            'task': str(comment.task.id),
            'content': 'Updated content',
        }
        response = authenticated_admin_client.put(
            comment_detail_url(comment.id), data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        comment.refresh_from_db()
        assert comment.content == 'Updated content'

    def test_delete_comment(self, authenticated_admin_client, admin_user):
        """Test deleting a comment."""
        comment = TaskCommentFactory(author=admin_user)
        comment_id = comment.id
        response = authenticated_admin_client.delete(
            comment_detail_url(comment_id)
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TaskComment.objects.filter(id=comment_id).exists()

    def test_filter_comments_by_task(self, authenticated_admin_client):
        """Test filtering comments by task ID."""
        task1 = TaskFactory()
        task2 = TaskFactory()
        TaskCommentFactory(task=task1)
        TaskCommentFactory(task=task1)
        TaskCommentFactory(task=task2)

        response = authenticated_admin_client.get(
            TASK_COMMENTS_API_URL, {'task': str(task1.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) == 2

    def test_comment_requires_authentication(self, api_client):
        """Test that unauthenticated users cannot access comments."""
        response = api_client.get(TASK_COMMENTS_API_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
