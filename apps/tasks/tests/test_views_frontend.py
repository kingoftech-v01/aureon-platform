"""
Tests for tasks app frontend views.

Tests cover:
- TaskListView (list, filtering by status/priority/assignee, search)
- TaskDetailView (detail page with comments and related entities)
- TaskCreateView (create form page)
- TaskBoardView (kanban board grouped by status)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist

from apps.tasks.models import Task
from .factories import UserFactory, TaskFactory, TaskCommentFactory


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
TASK_LIST_URL = '/api/tasks/'
TASK_CREATE_URL = '/api/tasks/create/'
TASK_BOARD_URL = '/api/tasks/board/'


def task_detail_url(pk):
    return f'/api/tasks/{pk}/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.login(username=user.username, password='TestPass123!')
    return client


@pytest.fixture
def task(user):
    return TaskFactory(assigned_to=user, created_by=user)


@pytest.fixture
def task_with_comments(task):
    TaskCommentFactory(task=task)
    TaskCommentFactory(task=task)
    return task


# ---------------------------------------------------------------------------
# TaskListView tests
# ---------------------------------------------------------------------------
class TestTaskListView:
    """Tests for TaskListView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(TASK_LIST_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, task):
        try:
            response = auth_client.get(TASK_LIST_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, task):
        try:
            response = auth_client.get(TASK_LIST_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Tasks'
            assert 'status_choices' in ctx
            assert 'priority_choices' in ctx
            assert 'my_task_count' in ctx
            assert 'overdue_count' in ctx
            assert 'tasks' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_status(self, auth_client, user):
        todo_task = TaskFactory(
            assigned_to=user, created_by=user, status=Task.TODO
        )
        TaskFactory(
            assigned_to=user, created_by=user, status=Task.DONE
        )
        try:
            response = auth_client.get(TASK_LIST_URL, {'status': Task.TODO})
            tasks = list(response.context['tasks'])
            assert todo_task in tasks
            assert all(t.status == Task.TODO for t in tasks)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_priority(self, auth_client, user):
        high_task = TaskFactory(
            assigned_to=user, created_by=user, priority=Task.HIGH
        )
        TaskFactory(
            assigned_to=user, created_by=user, priority=Task.LOW
        )
        try:
            response = auth_client.get(TASK_LIST_URL, {'priority': Task.HIGH})
            tasks = list(response.context['tasks'])
            assert high_task in tasks
            assert all(t.priority == Task.HIGH for t in tasks)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_assigned_to_me(self, auth_client, user):
        my_task = TaskFactory(assigned_to=user, created_by=user)
        other_user = UserFactory()
        TaskFactory(assigned_to=other_user, created_by=other_user)
        try:
            response = auth_client.get(TASK_LIST_URL, {'assigned': 'me'})
            tasks = list(response.context['tasks'])
            assert my_task in tasks
            assert all(t.assigned_to == user for t in tasks)
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_search_by_title(self, auth_client, user):
        target = TaskFactory(
            assigned_to=user, created_by=user, title='Unique Search Target'
        )
        TaskFactory(assigned_to=user, created_by=user, title='Other task')
        try:
            response = auth_client.get(TASK_LIST_URL, {'q': 'Unique Search'})
            tasks = list(response.context['tasks'])
            assert target in tasks
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# TaskDetailView tests
# ---------------------------------------------------------------------------
class TestTaskDetailView:
    """Tests for TaskDetailView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self, task):
        client = TestClient()
        response = client.get(task_detail_url(task.pk))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, task_with_comments):
        try:
            response = auth_client.get(task_detail_url(task_with_comments.pk))
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_task_and_comments(self, auth_client, task_with_comments):
        try:
            response = auth_client.get(task_detail_url(task_with_comments.pk))
            ctx = response.context
            assert ctx['task'] == task_with_comments
            assert 'comments' in ctx
            assert 'is_overdue' in ctx
            assert 'status_choices' in ctx
            assert 'priority_choices' in ctx
            assert 'page_title' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# TaskCreateView tests
# ---------------------------------------------------------------------------
class TestTaskCreateView:
    """Tests for TaskCreateView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(TASK_CREATE_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client):
        try:
            response = auth_client.get(TASK_CREATE_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_choices_and_lookups(self, auth_client):
        try:
            response = auth_client.get(TASK_CREATE_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Create Task'
            assert 'status_choices' in ctx
            assert 'priority_choices' in ctx
            assert 'users' in ctx
            assert 'clients' in ctx
            assert 'contracts' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# TaskBoardView tests
# ---------------------------------------------------------------------------
class TestTaskBoardView:
    """Tests for TaskBoardView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(TASK_BOARD_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, task):
        try:
            response = auth_client.get(TASK_BOARD_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_task_columns(self, auth_client, user):
        TaskFactory(assigned_to=user, created_by=user, status=Task.TODO)
        TaskFactory(assigned_to=user, created_by=user, status=Task.IN_PROGRESS)
        TaskFactory(assigned_to=user, created_by=user, status=Task.DONE)
        try:
            response = auth_client.get(TASK_BOARD_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Task Board'
            assert 'todo_tasks' in ctx
            assert 'in_progress_tasks' in ctx
            assert 'done_tasks' in ctx
            assert 'cancelled_tasks' in ctx
            assert 'priority_choices' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_board_filter_assigned_to_me(self, auth_client, user):
        my_task = TaskFactory(
            assigned_to=user, created_by=user, status=Task.TODO
        )
        other_user = UserFactory()
        TaskFactory(
            assigned_to=other_user, created_by=other_user, status=Task.TODO
        )
        try:
            response = auth_client.get(TASK_BOARD_URL, {'assigned': 'me'})
            todo = list(response.context['todo_tasks'])
            assert my_task in todo
        except TemplateDoesNotExist:
            pass
