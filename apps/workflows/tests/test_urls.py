"""
Tests for workflows app URL configuration.

Tests cover:
- URL resolution for all URL patterns
- URL reverse for all named URL patterns
"""

import uuid
import pytest
from django.urls import reverse, resolve


# ============================================================================
# Workflow URL Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowURLs:
    """Tests for Workflow URL patterns."""

    def test_workflow_list_url_reverse(self):
        """Test reverse for workflow-list."""
        url = reverse('workflows:workflow-list')
        assert url == '/api/workflows/workflows/'

    def test_workflow_list_url_resolve(self):
        """Test resolve for workflow list URL."""
        match = resolve('/api/workflows/workflows/')
        assert match.view_name == 'workflows:workflow-list'

    def test_workflow_detail_url_reverse(self):
        """Test reverse for workflow-detail."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-detail', args=[pk])
        assert str(pk) in url

    def test_workflow_detail_url_resolve(self):
        """Test resolve for workflow detail URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflows/{pk}/')
        assert match.view_name == 'workflows:workflow-detail'

    def test_workflow_activate_url_reverse(self):
        """Test reverse for workflow-activate."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-activate', args=[pk])
        assert 'activate' in url

    def test_workflow_activate_url_resolve(self):
        """Test resolve for workflow activate URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflows/{pk}/activate/')
        assert match.view_name == 'workflows:workflow-activate'

    def test_workflow_deactivate_url_reverse(self):
        """Test reverse for workflow-deactivate."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-deactivate', args=[pk])
        assert 'deactivate' in url

    def test_workflow_deactivate_url_resolve(self):
        """Test resolve for workflow deactivate URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflows/{pk}/deactivate/')
        assert match.view_name == 'workflows:workflow-deactivate'

    def test_workflow_execute_url_reverse(self):
        """Test reverse for workflow-execute."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-execute', args=[pk])
        assert 'execute' in url

    def test_workflow_execute_url_resolve(self):
        """Test resolve for workflow execute URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflows/{pk}/execute/')
        assert match.view_name == 'workflows:workflow-execute'

    def test_workflow_executions_url_reverse(self):
        """Test reverse for workflow-executions."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-executions', args=[pk])
        assert 'executions' in url

    def test_workflow_executions_url_resolve(self):
        """Test resolve for workflow executions URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflows/{pk}/executions/')
        assert match.view_name == 'workflows:workflow-executions'


# ============================================================================
# WorkflowAction URL Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionURLs:
    """Tests for WorkflowAction URL patterns."""

    def test_action_list_url_reverse(self):
        """Test reverse for workflow-action-list."""
        url = reverse('workflows:workflow-action-list')
        assert url == '/api/workflows/workflow-actions/'

    def test_action_list_url_resolve(self):
        """Test resolve for workflow action list URL."""
        match = resolve('/api/workflows/workflow-actions/')
        assert match.view_name == 'workflows:workflow-action-list'

    def test_action_detail_url_reverse(self):
        """Test reverse for workflow-action-detail."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-action-detail', args=[pk])
        assert str(pk) in url

    def test_action_detail_url_resolve(self):
        """Test resolve for workflow action detail URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflow-actions/{pk}/')
        assert match.view_name == 'workflows:workflow-action-detail'


# ============================================================================
# WorkflowExecution URL Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowExecutionURLs:
    """Tests for WorkflowExecution URL patterns."""

    def test_execution_list_url_reverse(self):
        """Test reverse for workflow-execution-list."""
        url = reverse('workflows:workflow-execution-list')
        assert url == '/api/workflows/workflow-executions/'

    def test_execution_list_url_resolve(self):
        """Test resolve for workflow execution list URL."""
        match = resolve('/api/workflows/workflow-executions/')
        assert match.view_name == 'workflows:workflow-execution-list'

    def test_execution_detail_url_reverse(self):
        """Test reverse for workflow-execution-detail."""
        pk = uuid.uuid4()
        url = reverse('workflows:workflow-execution-detail', args=[pk])
        assert str(pk) in url

    def test_execution_detail_url_resolve(self):
        """Test resolve for workflow execution detail URL."""
        pk = uuid.uuid4()
        match = resolve(f'/api/workflows/workflow-executions/{pk}/')
        assert match.view_name == 'workflows:workflow-execution-detail'
