"""
Tests for workflows app API views.

Tests cover:
- WorkflowViewSet CRUD operations
- WorkflowViewSet custom actions (activate, deactivate, execute, executions)
- WorkflowActionViewSet CRUD operations
- WorkflowExecutionViewSet list and retrieve
- Permission tests (authentication required)
- Filtering and search
"""

import uuid
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.workflows.models import (
    Workflow,
    WorkflowAction,
    WorkflowExecution,
)
from .factories import (
    WorkflowFactory,
    WorkflowActionFactory,
    WorkflowExecutionFactory,
    WorkflowActionExecutionFactory,
    UserFactory,
)


WORKFLOW_LIST_URL = '/api/workflows/workflows/'
WORKFLOW_ACTION_LIST_URL = '/api/workflows/workflow-actions/'
WORKFLOW_EXECUTION_LIST_URL = '/api/workflows/workflow-executions/'


def workflow_detail_url(workflow_id):
    return f'{WORKFLOW_LIST_URL}{workflow_id}/'


def workflow_action_detail_url(action_id):
    return f'{WORKFLOW_ACTION_LIST_URL}{action_id}/'


def workflow_execution_detail_url(execution_id):
    return f'{WORKFLOW_EXECUTION_LIST_URL}{execution_id}/'


@pytest.fixture
def user(db):
    return UserFactory(is_staff=True)


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def unauthenticated_client():
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    return client


# ============================================================================
# WorkflowViewSet CRUD Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowViewSetCRUD:
    """Tests for Workflow CRUD operations."""

    def test_list_workflows(self, authenticated_client, user):
        """Test listing workflows."""
        WorkflowFactory(owner=user)
        WorkflowFactory(owner=user)

        response = authenticated_client.get(WORKFLOW_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 2

    def test_list_workflows_empty(self, authenticated_client):
        """Test listing workflows when none exist."""
        response = authenticated_client.get(WORKFLOW_LIST_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_workflow(self, authenticated_client, user):
        """Test retrieving a specific workflow."""
        workflow = WorkflowFactory(owner=user, name='Retrieve Test')
        WorkflowActionFactory(workflow=workflow, order=0)

        response = authenticated_client.get(workflow_detail_url(workflow.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Retrieve Test'
        assert 'actions' in response.data

    def test_create_workflow(self, authenticated_client):
        """Test creating a workflow."""
        data = {
            'name': 'New Workflow',
            'description': 'Test description',
            'trigger_type': Workflow.INVOICE_PAID,
            'is_active': True,
            'trigger_config': {},
        }

        response = authenticated_client.post(WORKFLOW_LIST_URL, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Workflow.objects.filter(name='New Workflow').exists()

    def test_create_workflow_minimal(self, authenticated_client):
        """Test creating a workflow with minimal data."""
        data = {
            'name': 'Minimal WF',
            'trigger_type': Workflow.MANUAL,
        }

        response = authenticated_client.post(WORKFLOW_LIST_URL, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_workflow_invalid(self, authenticated_client):
        """Test creating a workflow with invalid data."""
        data = {
            'description': 'Missing name and trigger_type',
        }

        response = authenticated_client.post(WORKFLOW_LIST_URL, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_workflow(self, authenticated_client, user):
        """Test updating a workflow."""
        workflow = WorkflowFactory(owner=user, name='Original')

        data = {
            'name': 'Updated',
            'trigger_type': Workflow.CLIENT_CREATED,
        }

        response = authenticated_client.put(
            workflow_detail_url(workflow.id), data, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        workflow.refresh_from_db()
        assert workflow.name == 'Updated'

    def test_partial_update_workflow(self, authenticated_client, user):
        """Test partial update of a workflow."""
        workflow = WorkflowFactory(owner=user, name='Original', is_active=True)

        response = authenticated_client.patch(
            workflow_detail_url(workflow.id),
            {'is_active': False},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        workflow.refresh_from_db()
        assert workflow.is_active is False
        assert workflow.name == 'Original'

    def test_delete_workflow(self, authenticated_client, user):
        """Test deleting a workflow."""
        workflow = WorkflowFactory(owner=user)

        response = authenticated_client.delete(workflow_detail_url(workflow.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Workflow.objects.filter(id=workflow.id).exists()

    def test_retrieve_nonexistent_workflow(self, authenticated_client):
        """Test retrieving a nonexistent workflow."""
        fake_id = uuid.uuid4()
        response = authenticated_client.get(workflow_detail_url(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# WorkflowViewSet Custom Action Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowViewSetActions:
    """Tests for Workflow custom actions."""

    def test_activate_workflow(self, authenticated_client, user):
        """Test activating a workflow."""
        workflow = WorkflowFactory(owner=user, is_active=False)

        response = authenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/activate/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True

        workflow.refresh_from_db()
        assert workflow.is_active is True

    def test_deactivate_workflow(self, authenticated_client, user):
        """Test deactivating a workflow."""
        workflow = WorkflowFactory(owner=user, is_active=True)

        response = authenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/deactivate/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

        workflow.refresh_from_db()
        assert workflow.is_active is False

    def test_execute_workflow(self, authenticated_client, user):
        """Test manually executing a workflow."""
        workflow = WorkflowFactory(owner=user)

        response = authenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/execute/',
            {'trigger_data': {'key': 'value'}},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == WorkflowExecution.PENDING
        assert response.data['workflow'] == str(workflow.id)
        assert WorkflowExecution.objects.filter(workflow=workflow).count() == 1

    def test_execute_workflow_without_trigger_data(self, authenticated_client, user):
        """Test executing a workflow without trigger data."""
        workflow = WorkflowFactory(owner=user)

        response = authenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/execute/',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['trigger_data'] == {}

    def test_executions_action(self, authenticated_client, user):
        """Test getting executions for a workflow."""
        workflow = WorkflowFactory(owner=user)
        WorkflowExecutionFactory(workflow=workflow)
        WorkflowExecutionFactory(workflow=workflow)

        response = authenticated_client.get(
            f'{WORKFLOW_LIST_URL}{workflow.id}/executions/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_executions_action_empty(self, authenticated_client, user):
        """Test getting executions when none exist."""
        workflow = WorkflowFactory(owner=user)

        response = authenticated_client.get(
            f'{WORKFLOW_LIST_URL}{workflow.id}/executions/'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


# ============================================================================
# WorkflowViewSet Permission Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowViewSetPermissions:
    """Tests for Workflow permissions."""

    def test_list_unauthenticated(self, unauthenticated_client):
        """Test listing workflows without authentication."""
        response = unauthenticated_client.get(WORKFLOW_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_unauthenticated(self, unauthenticated_client):
        """Test creating workflows without authentication."""
        response = unauthenticated_client.post(WORKFLOW_LIST_URL, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_unauthenticated(self, unauthenticated_client):
        """Test retrieving workflow without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.get(workflow_detail_url(workflow.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_unauthenticated(self, unauthenticated_client):
        """Test updating workflow without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.put(workflow_detail_url(workflow.id), {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_unauthenticated(self, unauthenticated_client):
        """Test deleting workflow without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.delete(workflow_detail_url(workflow.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_activate_unauthenticated(self, unauthenticated_client):
        """Test activate action without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/activate/'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_deactivate_unauthenticated(self, unauthenticated_client):
        """Test deactivate action without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/deactivate/'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_execute_unauthenticated(self, unauthenticated_client):
        """Test execute action without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.post(
            f'{WORKFLOW_LIST_URL}{workflow.id}/execute/'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_executions_unauthenticated(self, unauthenticated_client):
        """Test executions action without authentication."""
        workflow = WorkflowFactory()
        response = unauthenticated_client.get(
            f'{WORKFLOW_LIST_URL}{workflow.id}/executions/'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# WorkflowViewSet Filtering and Search Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowViewSetFilterSearch:
    """Tests for Workflow filtering and search."""

    def test_search_by_name(self, authenticated_client, user):
        """Test searching workflows by name."""
        WorkflowFactory(owner=user, name='Payment Automation')
        WorkflowFactory(owner=user, name='Invoice Reminder')

        response = authenticated_client.get(f'{WORKFLOW_LIST_URL}?search=Payment')

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert any('Payment' in r['name'] for r in results)

    def test_search_by_description(self, authenticated_client, user):
        """Test searching workflows by description."""
        WorkflowFactory(owner=user, description='Handles payment processing')

        response = authenticated_client.get(f'{WORKFLOW_LIST_URL}?search=payment processing')

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_trigger_type(self, authenticated_client, user):
        """Test filtering by trigger_type."""
        WorkflowFactory(owner=user, trigger_type=Workflow.INVOICE_PAID)
        WorkflowFactory(owner=user, trigger_type=Workflow.CONTRACT_SIGNED)

        response = authenticated_client.get(
            f'{WORKFLOW_LIST_URL}?trigger_type={Workflow.INVOICE_PAID}'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for r in results:
            assert r['trigger_type'] == Workflow.INVOICE_PAID

    def test_filter_by_is_active(self, authenticated_client, user):
        """Test filtering by is_active."""
        WorkflowFactory(owner=user, is_active=True)
        WorkflowFactory(owner=user, is_active=False)

        response = authenticated_client.get(f'{WORKFLOW_LIST_URL}?is_active=true')

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for r in results:
            assert r['is_active'] is True

    def test_filter_by_owner(self, authenticated_client, user):
        """Test filtering by owner."""
        WorkflowFactory(owner=user)
        other_user = UserFactory()
        WorkflowFactory(owner=other_user)

        response = authenticated_client.get(f'{WORKFLOW_LIST_URL}?owner={user.id}')

        assert response.status_code == status.HTTP_200_OK

    def test_ordering_by_name(self, authenticated_client, user):
        """Test ordering by name."""
        WorkflowFactory(owner=user, name='Zebra')
        WorkflowFactory(owner=user, name='Alpha')

        response = authenticated_client.get(f'{WORKFLOW_LIST_URL}?ordering=name')

        assert response.status_code == status.HTTP_200_OK

    def test_ordering_by_created_at(self, authenticated_client, user):
        """Test ordering by created_at."""
        WorkflowFactory(owner=user)
        WorkflowFactory(owner=user)

        response = authenticated_client.get(f'{WORKFLOW_LIST_URL}?ordering=-created_at')

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# WorkflowActionViewSet CRUD Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionViewSetCRUD:
    """Tests for WorkflowAction CRUD operations."""

    def test_list_actions(self, authenticated_client, user):
        """Test listing workflow actions."""
        workflow = WorkflowFactory(owner=user)
        WorkflowActionFactory(workflow=workflow, order=0)
        WorkflowActionFactory(workflow=workflow, order=1)

        response = authenticated_client.get(WORKFLOW_ACTION_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 2

    def test_retrieve_action(self, authenticated_client, user):
        """Test retrieving a workflow action."""
        workflow = WorkflowFactory(owner=user)
        action = WorkflowActionFactory(
            workflow=workflow,
            action_type=WorkflowAction.SEND_EMAIL,
            order=0,
        )

        response = authenticated_client.get(workflow_action_detail_url(action.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['action_type'] == WorkflowAction.SEND_EMAIL

    def test_create_action(self, authenticated_client, user):
        """Test creating a workflow action."""
        workflow = WorkflowFactory(owner=user)
        data = {
            'workflow': str(workflow.id),
            'action_type': WorkflowAction.CREATE_TASK,
            'action_config': {'task_name': 'Follow up'},
            'order': 0,
            'delay_minutes': 5,
            'is_active': True,
        }

        response = authenticated_client.post(
            WORKFLOW_ACTION_LIST_URL, data, format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['action_type'] == WorkflowAction.CREATE_TASK

    def test_update_action(self, authenticated_client, user):
        """Test updating a workflow action."""
        workflow = WorkflowFactory(owner=user)
        action = WorkflowActionFactory(workflow=workflow, order=0)

        data = {
            'workflow': str(workflow.id),
            'action_type': WorkflowAction.WEBHOOK_CALL,
            'action_config': {'url': 'https://example.com/hook'},
            'order': 0,
            'delay_minutes': 30,
            'is_active': False,
        }

        response = authenticated_client.put(
            workflow_action_detail_url(action.id), data, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['action_type'] == WorkflowAction.WEBHOOK_CALL
        assert response.data['delay_minutes'] == 30

    def test_partial_update_action(self, authenticated_client, user):
        """Test partial update of a workflow action."""
        workflow = WorkflowFactory(owner=user)
        action = WorkflowActionFactory(workflow=workflow, order=0, is_active=True)

        response = authenticated_client.patch(
            workflow_action_detail_url(action.id),
            {'is_active': False},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    def test_delete_action(self, authenticated_client, user):
        """Test deleting a workflow action."""
        workflow = WorkflowFactory(owner=user)
        action = WorkflowActionFactory(workflow=workflow, order=0)

        response = authenticated_client.delete(workflow_action_detail_url(action.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not WorkflowAction.objects.filter(id=action.id).exists()

    def test_filter_by_workflow(self, authenticated_client, user):
        """Test filtering actions by workflow."""
        wf1 = WorkflowFactory(owner=user)
        wf2 = WorkflowFactory(owner=user)
        WorkflowActionFactory(workflow=wf1, order=0)
        WorkflowActionFactory(workflow=wf2, order=0)

        response = authenticated_client.get(
            f'{WORKFLOW_ACTION_LIST_URL}?workflow={wf1.id}'
        )

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        for r in results:
            assert r['workflow'] == str(wf1.id)

    def test_filter_by_action_type(self, authenticated_client, user):
        """Test filtering actions by action_type."""
        workflow = WorkflowFactory(owner=user)
        WorkflowActionFactory(
            workflow=workflow, action_type=WorkflowAction.SEND_EMAIL, order=0
        )
        WorkflowActionFactory(
            workflow=workflow, action_type=WorkflowAction.CREATE_TASK, order=1
        )

        response = authenticated_client.get(
            f'{WORKFLOW_ACTION_LIST_URL}?action_type={WorkflowAction.SEND_EMAIL}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_is_active(self, authenticated_client, user):
        """Test filtering actions by is_active."""
        workflow = WorkflowFactory(owner=user)
        WorkflowActionFactory(workflow=workflow, is_active=True, order=0)
        WorkflowActionFactory(workflow=workflow, is_active=False, order=1)

        response = authenticated_client.get(
            f'{WORKFLOW_ACTION_LIST_URL}?is_active=true'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# WorkflowActionViewSet Permission Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionViewSetPermissions:
    """Tests for WorkflowAction permissions."""

    def test_list_unauthenticated(self, unauthenticated_client):
        """Test listing actions without authentication."""
        response = unauthenticated_client.get(WORKFLOW_ACTION_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_unauthenticated(self, unauthenticated_client):
        """Test creating action without authentication."""
        response = unauthenticated_client.post(WORKFLOW_ACTION_LIST_URL, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_unauthenticated(self, unauthenticated_client):
        """Test retrieving action without authentication."""
        action = WorkflowActionFactory()
        response = unauthenticated_client.get(workflow_action_detail_url(action.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_unauthenticated(self, unauthenticated_client):
        """Test deleting action without authentication."""
        action = WorkflowActionFactory()
        response = unauthenticated_client.delete(workflow_action_detail_url(action.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# WorkflowExecutionViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowExecutionViewSet:
    """Tests for WorkflowExecution list and retrieve."""

    def test_list_executions(self, authenticated_client, user):
        """Test listing workflow executions."""
        workflow = WorkflowFactory(owner=user)
        WorkflowExecutionFactory(workflow=workflow)
        WorkflowExecutionFactory(workflow=workflow)

        response = authenticated_client.get(WORKFLOW_EXECUTION_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) >= 2

    def test_retrieve_execution(self, authenticated_client, user):
        """Test retrieving an execution."""
        workflow = WorkflowFactory(owner=user)
        execution = WorkflowExecutionFactory(workflow=workflow)

        response = authenticated_client.get(
            workflow_execution_detail_url(execution.id)
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['workflow'] == str(workflow.id)

    def test_execution_viewset_is_read_only(self, authenticated_client, user):
        """Test execution viewset does not allow create."""
        workflow = WorkflowFactory(owner=user)
        data = {
            'workflow': str(workflow.id),
            'status': WorkflowExecution.PENDING,
        }

        response = authenticated_client.post(
            WORKFLOW_EXECUTION_LIST_URL, data, format='json'
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_execution_viewset_no_delete(self, authenticated_client, user):
        """Test execution viewset does not allow delete."""
        workflow = WorkflowFactory(owner=user)
        execution = WorkflowExecutionFactory(workflow=workflow)

        response = authenticated_client.delete(
            workflow_execution_detail_url(execution.id)
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_execution_viewset_no_update(self, authenticated_client, user):
        """Test execution viewset does not allow update."""
        workflow = WorkflowFactory(owner=user)
        execution = WorkflowExecutionFactory(workflow=workflow)

        response = authenticated_client.put(
            workflow_execution_detail_url(execution.id), {}, format='json'
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_filter_by_workflow(self, authenticated_client, user):
        """Test filtering executions by workflow."""
        wf1 = WorkflowFactory(owner=user)
        wf2 = WorkflowFactory(owner=user)
        WorkflowExecutionFactory(workflow=wf1)
        WorkflowExecutionFactory(workflow=wf2)

        response = authenticated_client.get(
            f'{WORKFLOW_EXECUTION_LIST_URL}?workflow={wf1.id}'
        )

        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_status(self, authenticated_client, user):
        """Test filtering executions by status."""
        workflow = WorkflowFactory(owner=user)
        WorkflowExecutionFactory(workflow=workflow, status=WorkflowExecution.COMPLETED)
        WorkflowExecutionFactory(workflow=workflow, status=WorkflowExecution.FAILED)

        response = authenticated_client.get(
            f'{WORKFLOW_EXECUTION_LIST_URL}?status={WorkflowExecution.COMPLETED}'
        )

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# WorkflowExecutionViewSet Permission Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowExecutionViewSetPermissions:
    """Tests for WorkflowExecution permissions."""

    def test_list_unauthenticated(self, unauthenticated_client):
        """Test listing executions without authentication."""
        response = unauthenticated_client.get(WORKFLOW_EXECUTION_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_unauthenticated(self, unauthenticated_client):
        """Test retrieving execution without authentication."""
        execution = WorkflowExecutionFactory()
        response = unauthenticated_client.get(
            workflow_execution_detail_url(execution.id)
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
