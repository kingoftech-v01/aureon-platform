"""
Tests for tasks app URL configuration.

Tests cover:
- API router URL resolution for TaskViewSet and TaskCommentViewSet
- Custom action URL resolution (complete, reopen, stats, comments)
- Frontend URL resolution (task_list, task_create, task_board, task_detail)
- URL reversibility via django.urls.reverse
- Correct view names and app namespace
"""

import uuid
import pytest
from django.urls import reverse, resolve


# ============================================================================
# API Router URL Resolution Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskAPIURLs:
    """Tests for Task API URL resolution."""

    def test_task_list_url_resolves(self):
        """Test that the task list API URL resolves correctly."""
        url = reverse('tasks:task-list')
        assert '/api/' in url
        assert '/tasks/' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-list'

    def test_task_detail_url_resolves(self):
        """Test that the task detail API URL resolves correctly."""
        task_id = uuid.uuid4()
        url = reverse('tasks:task-detail', kwargs={'pk': task_id})
        assert str(task_id) in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-detail'

    def test_task_complete_url_resolves(self):
        """Test that the task complete action URL resolves correctly."""
        task_id = uuid.uuid4()
        url = reverse('tasks:task-complete', kwargs={'pk': task_id})
        assert 'complete' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-complete'

    def test_task_reopen_url_resolves(self):
        """Test that the task reopen action URL resolves correctly."""
        task_id = uuid.uuid4()
        url = reverse('tasks:task-reopen', kwargs={'pk': task_id})
        assert 'reopen' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-reopen'

    def test_task_stats_url_resolves(self):
        """Test that the task stats action URL resolves correctly."""
        url = reverse('tasks:task-stats')
        assert 'stats' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-stats'

    def test_task_comments_action_url_resolves(self):
        """Test that the task comments action URL resolves correctly."""
        task_id = uuid.uuid4()
        url = reverse('tasks:task-comments', kwargs={'pk': task_id})
        assert 'comments' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-comments'


# ============================================================================
# TaskComment API URL Resolution Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskCommentAPIURLs:
    """Tests for TaskComment API URL resolution."""

    def test_task_comment_list_url_resolves(self):
        """Test that the task comment list URL resolves correctly."""
        url = reverse('tasks:task-comment-list')
        assert 'task-comments' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-comment-list'

    def test_task_comment_detail_url_resolves(self):
        """Test that the task comment detail URL resolves correctly."""
        comment_id = uuid.uuid4()
        url = reverse('tasks:task-comment-detail', kwargs={'pk': comment_id})
        assert str(comment_id) in url
        resolved = resolve(url)
        assert resolved.url_name == 'task-comment-detail'


# ============================================================================
# Frontend URL Resolution Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskFrontendURLs:
    """Tests for Task frontend URL resolution."""

    def test_task_list_frontend_url(self):
        """Test that the frontend task list URL resolves correctly."""
        url = reverse('tasks:task_list')
        resolved = resolve(url)
        assert resolved.url_name == 'task_list'

    def test_task_create_frontend_url(self):
        """Test that the frontend task create URL resolves correctly."""
        url = reverse('tasks:task_create')
        assert 'create' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task_create'

    def test_task_board_frontend_url(self):
        """Test that the frontend task board URL resolves correctly."""
        url = reverse('tasks:task_board')
        assert 'board' in url
        resolved = resolve(url)
        assert resolved.url_name == 'task_board'

    def test_task_detail_frontend_url(self):
        """Test that the frontend task detail URL resolves with a UUID."""
        task_id = uuid.uuid4()
        url = reverse('tasks:task_detail', kwargs={'pk': task_id})
        assert str(task_id) in url
        resolved = resolve(url)
        assert resolved.url_name == 'task_detail'


# ============================================================================
# Namespace Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskURLNamespace:
    """Tests for the tasks app URL namespace."""

    def test_app_name_is_tasks(self):
        """Test that the app namespace is 'tasks'."""
        # Verify reverse works with the 'tasks:' namespace prefix
        url = reverse('tasks:task-list')
        assert url is not None

    def test_all_api_endpoints_reversible(self):
        """Test that all expected API endpoints can be reversed."""
        task_id = uuid.uuid4()

        # List/create endpoints (no kwargs)
        assert reverse('tasks:task-list')
        assert reverse('tasks:task-comment-list')
        assert reverse('tasks:task-stats')

        # Detail endpoints (with pk)
        assert reverse('tasks:task-detail', kwargs={'pk': task_id})
        assert reverse('tasks:task-comment-detail', kwargs={'pk': task_id})

        # Custom actions (with pk)
        assert reverse('tasks:task-complete', kwargs={'pk': task_id})
        assert reverse('tasks:task-reopen', kwargs={'pk': task_id})
        assert reverse('tasks:task-comments', kwargs={'pk': task_id})
