"""
Tests for workflows app serializers.

Tests cover:
- WorkflowListSerializer (actions_count)
- WorkflowDetailSerializer (nested actions)
- WorkflowCreateUpdateSerializer validation
- WorkflowActionSerializer
- WorkflowExecutionSerializer (duration)
- WorkflowActionExecutionSerializer
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from apps.workflows.serializers import (
    WorkflowListSerializer,
    WorkflowDetailSerializer,
    WorkflowCreateUpdateSerializer,
    WorkflowActionSerializer,
    WorkflowExecutionSerializer,
    WorkflowActionExecutionSerializer,
)
from apps.workflows.models import (
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowActionExecution,
)
from .factories import (
    WorkflowFactory,
    WorkflowActionFactory,
    WorkflowExecutionFactory,
    WorkflowActionExecutionFactory,
    UserFactory,
)


# ============================================================================
# WorkflowListSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowListSerializer:
    """Tests for WorkflowListSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        workflow = WorkflowFactory()
        serializer = WorkflowListSerializer(workflow)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'trigger_type' in data
        assert 'is_active' in data
        assert 'created_at' in data
        assert 'actions_count' in data

    def test_actions_count_zero(self):
        """Test actions_count returns 0 when no actions."""
        workflow = WorkflowFactory()
        serializer = WorkflowListSerializer(workflow)
        assert serializer.data['actions_count'] == 0

    def test_actions_count_multiple(self):
        """Test actions_count with multiple actions."""
        workflow = WorkflowFactory()
        WorkflowActionFactory(workflow=workflow, order=0)
        WorkflowActionFactory(workflow=workflow, order=1)
        WorkflowActionFactory(workflow=workflow, order=2)

        serializer = WorkflowListSerializer(workflow)
        assert serializer.data['actions_count'] == 3

    def test_serializer_data_values(self):
        """Test serializer data values are correct."""
        workflow = WorkflowFactory(
            name='Test Serializer WF',
            trigger_type=Workflow.INVOICE_PAID,
            is_active=False,
        )
        serializer = WorkflowListSerializer(workflow)
        data = serializer.data

        assert data['name'] == 'Test Serializer WF'
        assert data['trigger_type'] == Workflow.INVOICE_PAID
        assert data['is_active'] is False


# ============================================================================
# WorkflowDetailSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowDetailSerializer:
    """Tests for WorkflowDetailSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        workflow = WorkflowFactory()
        serializer = WorkflowDetailSerializer(workflow)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'description' in data
        assert 'is_active' in data
        assert 'trigger_type' in data
        assert 'trigger_config' in data
        assert 'owner' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'actions' in data

    def test_nested_actions_empty(self):
        """Test nested actions are empty when no actions exist."""
        workflow = WorkflowFactory()
        serializer = WorkflowDetailSerializer(workflow)
        assert serializer.data['actions'] == []

    def test_nested_actions_present(self):
        """Test nested actions are serialized correctly."""
        workflow = WorkflowFactory()
        action = WorkflowActionFactory(
            workflow=workflow,
            action_type=WorkflowAction.CREATE_TASK,
            order=0,
        )
        serializer = WorkflowDetailSerializer(workflow)
        actions = serializer.data['actions']

        assert len(actions) == 1
        assert actions[0]['action_type'] == WorkflowAction.CREATE_TASK
        assert actions[0]['order'] == 0

    def test_nested_actions_ordering(self):
        """Test nested actions maintain ordering."""
        workflow = WorkflowFactory()
        WorkflowActionFactory(workflow=workflow, order=2, action_type=WorkflowAction.WEBHOOK_CALL)
        WorkflowActionFactory(workflow=workflow, order=0, action_type=WorkflowAction.SEND_EMAIL)
        WorkflowActionFactory(workflow=workflow, order=1, action_type=WorkflowAction.CREATE_TASK)

        serializer = WorkflowDetailSerializer(workflow)
        actions = serializer.data['actions']

        assert len(actions) == 3
        assert actions[0]['order'] == 0
        assert actions[1]['order'] == 1
        assert actions[2]['order'] == 2

    def test_detail_serializer_data_values(self):
        """Test detail serializer includes all workflow data."""
        user = UserFactory()
        workflow = WorkflowFactory(
            name='Detailed WF',
            description='Full details',
            trigger_type=Workflow.MANUAL,
            trigger_config={'manual': True},
            owner=user,
        )
        serializer = WorkflowDetailSerializer(workflow)
        data = serializer.data

        assert data['name'] == 'Detailed WF'
        assert data['description'] == 'Full details'
        assert data['trigger_type'] == Workflow.MANUAL
        assert data['trigger_config'] == {'manual': True}
        assert data['owner'] == str(user.id)


# ============================================================================
# WorkflowCreateUpdateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowCreateUpdateSerializer:
    """Tests for WorkflowCreateUpdateSerializer."""

    def test_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'name': 'New Workflow',
            'description': 'A new workflow',
            'trigger_type': Workflow.CONTRACT_SIGNED,
            'trigger_config': {},
            'is_active': True,
        }
        serializer = WorkflowCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_required_fields(self):
        """Test serializer requires name and trigger_type."""
        serializer = WorkflowCreateUpdateSerializer(data={})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'trigger_type' in serializer.errors

    def test_valid_trigger_type(self):
        """Test serializer validates trigger_type choices."""
        data = {
            'name': 'WF',
            'trigger_type': 'invalid_trigger',
        }
        serializer = WorkflowCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'trigger_type' in serializer.errors

    def test_serializer_fields(self):
        """Test serializer only includes expected fields."""
        serializer = WorkflowCreateUpdateSerializer()
        expected_fields = {'name', 'description', 'trigger_type', 'trigger_config', 'is_active'}
        assert set(serializer.fields.keys()) == expected_fields

    def test_create_workflow(self):
        """Test creating workflow via serializer."""
        data = {
            'name': 'Created via Serializer',
            'trigger_type': Workflow.PAYMENT_RECEIVED,
            'is_active': True,
        }
        serializer = WorkflowCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        workflow = serializer.save()
        assert workflow.name == 'Created via Serializer'
        assert workflow.trigger_type == Workflow.PAYMENT_RECEIVED

    def test_update_workflow(self):
        """Test updating workflow via serializer."""
        workflow = WorkflowFactory(name='Original')
        data = {
            'name': 'Updated',
            'trigger_type': Workflow.INVOICE_OVERDUE,
        }
        serializer = WorkflowCreateUpdateSerializer(workflow, data=data)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.name == 'Updated'
        assert updated.trigger_type == Workflow.INVOICE_OVERDUE

    def test_partial_update(self):
        """Test partial update via serializer."""
        workflow = WorkflowFactory(name='Original', is_active=True)
        serializer = WorkflowCreateUpdateSerializer(
            workflow, data={'is_active': False}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.is_active is False
        assert updated.name == 'Original'


# ============================================================================
# WorkflowActionSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionSerializer:
    """Tests for WorkflowActionSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        action = WorkflowActionFactory()
        serializer = WorkflowActionSerializer(action)
        data = serializer.data

        assert 'id' in data
        assert 'workflow' in data
        assert 'action_type' in data
        assert 'action_config' in data
        assert 'order' in data
        assert 'delay_minutes' in data
        assert 'is_active' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_read_only_fields(self):
        """Test read-only fields are correctly defined."""
        serializer = WorkflowActionSerializer()
        assert 'id' in serializer.Meta.read_only_fields
        assert 'created_at' in serializer.Meta.read_only_fields
        assert 'updated_at' in serializer.Meta.read_only_fields

    def test_valid_creation_data(self):
        """Test creating action with valid data."""
        workflow = WorkflowFactory()
        data = {
            'workflow': str(workflow.id),
            'action_type': WorkflowAction.SEND_NOTIFICATION,
            'action_config': {'message': 'Hello'},
            'order': 5,
            'delay_minutes': 10,
            'is_active': True,
        }
        serializer = WorkflowActionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_action_type(self):
        """Test serializer rejects invalid action_type."""
        workflow = WorkflowFactory()
        data = {
            'workflow': str(workflow.id),
            'action_type': 'invalid_type',
            'order': 0,
        }
        serializer = WorkflowActionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'action_type' in serializer.errors

    def test_serializer_data_values(self):
        """Test serializer returns correct values."""
        action = WorkflowActionFactory(
            action_type=WorkflowAction.WEBHOOK_CALL,
            delay_minutes=15,
            order=3,
        )
        serializer = WorkflowActionSerializer(action)
        data = serializer.data

        assert data['action_type'] == WorkflowAction.WEBHOOK_CALL
        assert data['delay_minutes'] == 15
        assert data['order'] == 3


# ============================================================================
# WorkflowExecutionSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowExecutionSerializer:
    """Tests for WorkflowExecutionSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        execution = WorkflowExecutionFactory()
        serializer = WorkflowExecutionSerializer(execution)
        data = serializer.data

        assert 'id' in data
        assert 'workflow' in data
        assert 'status' in data
        assert 'triggered_by' in data
        assert 'trigger_data' in data
        assert 'started_at' in data
        assert 'completed_at' in data
        assert 'error_message' in data
        assert 'created_at' in data
        assert 'duration' in data
        assert 'action_executions' in data

    def test_duration_with_timestamps(self):
        """Test duration field with both timestamps."""
        now = timezone.now()
        execution = WorkflowExecutionFactory(
            started_at=now - timedelta(hours=1),
            completed_at=now,
        )
        serializer = WorkflowExecutionSerializer(execution)
        assert serializer.data['duration'] is not None
        assert '1:00:00' in serializer.data['duration']

    def test_duration_without_timestamps(self):
        """Test duration field returns None when timestamps missing."""
        execution = WorkflowExecutionFactory(
            started_at=None,
            completed_at=None,
        )
        serializer = WorkflowExecutionSerializer(execution)
        assert serializer.data['duration'] is None

    def test_duration_with_only_started_at(self):
        """Test duration returns None with only started_at."""
        execution = WorkflowExecutionFactory(
            started_at=timezone.now(),
            completed_at=None,
        )
        serializer = WorkflowExecutionSerializer(execution)
        assert serializer.data['duration'] is None

    def test_nested_action_executions_empty(self):
        """Test action_executions is empty when no action executions exist."""
        execution = WorkflowExecutionFactory()
        serializer = WorkflowExecutionSerializer(execution)
        assert serializer.data['action_executions'] == []

    def test_nested_action_executions_present(self):
        """Test nested action executions are serialized."""
        workflow = WorkflowFactory()
        action = WorkflowActionFactory(workflow=workflow, order=0)
        execution = WorkflowExecutionFactory(workflow=workflow)
        ae = WorkflowActionExecutionFactory(
            execution=execution,
            action=action,
            status=WorkflowActionExecution.COMPLETED,
        )

        serializer = WorkflowExecutionSerializer(execution)
        aes = serializer.data['action_executions']

        assert len(aes) == 1
        assert aes[0]['status'] == WorkflowActionExecution.COMPLETED


# ============================================================================
# WorkflowActionExecutionSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionExecutionSerializer:
    """Tests for WorkflowActionExecutionSerializer."""

    def test_serializer_fields(self):
        """Test serializer returns expected fields."""
        ae = WorkflowActionExecutionFactory()
        serializer = WorkflowActionExecutionSerializer(ae)
        data = serializer.data

        assert 'id' in data
        assert 'execution' in data
        assert 'action' in data
        assert 'status' in data
        assert 'result_data' in data
        assert 'started_at' in data
        assert 'completed_at' in data
        assert 'error_message' in data

    def test_read_only_fields(self):
        """Test read-only fields."""
        serializer = WorkflowActionExecutionSerializer()
        assert 'id' in serializer.Meta.read_only_fields

    def test_serializer_data_values(self):
        """Test serializer returns correct values."""
        ae = WorkflowActionExecutionFactory(
            status=WorkflowActionExecution.FAILED,
            error_message='Timeout',
            result_data={'error_code': 500},
        )
        serializer = WorkflowActionExecutionSerializer(ae)
        data = serializer.data

        assert data['status'] == WorkflowActionExecution.FAILED
        assert data['error_message'] == 'Timeout'
        assert data['result_data'] == {'error_code': 500}
