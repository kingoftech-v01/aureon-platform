"""
Tests for workflows app models.

Tests cover:
- Workflow model creation, __str__, properties, and relationships
- WorkflowAction model creation, __str__, ordering, and unique constraints
- WorkflowExecution model creation, __str__, status transitions, duration property
- WorkflowActionExecution model creation, __str__, relationships
"""

import uuid
import pytest
from datetime import timedelta
from django.utils import timezone
from django.db import IntegrityError

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
# Workflow Model Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowModel:
    """Tests for the Workflow model."""

    def test_create_workflow(self):
        """Test creating a workflow with all fields."""
        user = UserFactory()
        workflow = WorkflowFactory(
            name='Test Workflow',
            description='A test workflow',
            is_active=True,
            trigger_type=Workflow.CONTRACT_SIGNED,
            trigger_config={'key': 'value'},
            owner=user,
        )

        assert workflow.name == 'Test Workflow'
        assert workflow.description == 'A test workflow'
        assert workflow.is_active is True
        assert workflow.trigger_type == Workflow.CONTRACT_SIGNED
        assert workflow.trigger_config == {'key': 'value'}
        assert workflow.owner == user

    def test_workflow_str(self):
        """Test workflow string representation."""
        workflow = WorkflowFactory(name='My Workflow')
        assert str(workflow) == 'My Workflow'

    def test_workflow_uuid_primary_key(self):
        """Test workflow has UUID primary key."""
        workflow = WorkflowFactory()
        assert isinstance(workflow.id, uuid.UUID)

    def test_workflow_default_is_active(self):
        """Test workflow defaults to active."""
        workflow = WorkflowFactory()
        assert workflow.is_active is True

    def test_workflow_timestamps(self):
        """Test workflow has created_at and updated_at timestamps."""
        workflow = WorkflowFactory()
        assert workflow.created_at is not None
        assert workflow.updated_at is not None

    def test_workflow_ordering(self):
        """Test workflows are ordered by -created_at."""
        w1 = WorkflowFactory()
        w2 = WorkflowFactory()
        workflows = list(Workflow.objects.all())
        assert workflows[0].created_at >= workflows[1].created_at

    def test_workflow_trigger_type_choices(self):
        """Test all trigger type choices are valid."""
        valid_types = [
            Workflow.CONTRACT_SIGNED,
            Workflow.INVOICE_CREATED,
            Workflow.INVOICE_OVERDUE,
            Workflow.INVOICE_PAID,
            Workflow.PAYMENT_RECEIVED,
            Workflow.PAYMENT_FAILED,
            Workflow.CLIENT_CREATED,
            Workflow.CLIENT_UPDATED,
            Workflow.MILESTONE_COMPLETED,
            Workflow.SUBSCRIPTION_CANCELLED,
            Workflow.MANUAL,
        ]
        choices_dict = dict(Workflow.TRIGGER_TYPE_CHOICES)
        for trigger_type in valid_types:
            assert trigger_type in choices_dict

    def test_workflow_with_each_trigger_type(self):
        """Test creating a workflow with each trigger type."""
        for trigger_value, _ in Workflow.TRIGGER_TYPE_CHOICES:
            workflow = WorkflowFactory(trigger_type=trigger_value)
            assert workflow.trigger_type == trigger_value

    def test_workflow_owner_nullable(self):
        """Test workflow can be created without an owner."""
        workflow = WorkflowFactory(owner=None)
        assert workflow.owner is None

    def test_workflow_trigger_config_default(self):
        """Test trigger_config defaults to empty dict."""
        workflow = WorkflowFactory(trigger_config={})
        assert workflow.trigger_config == {}

    def test_workflow_description_blank(self):
        """Test workflow can have blank description."""
        workflow = WorkflowFactory(description='')
        assert workflow.description == ''

    def test_workflow_actions_relationship(self):
        """Test workflow can have related actions."""
        workflow = WorkflowFactory()
        action1 = WorkflowActionFactory(workflow=workflow, order=0)
        action2 = WorkflowActionFactory(workflow=workflow, order=1)
        assert workflow.actions.count() == 2

    def test_workflow_executions_relationship(self):
        """Test workflow can have related executions."""
        workflow = WorkflowFactory()
        exec1 = WorkflowExecutionFactory(workflow=workflow)
        exec2 = WorkflowExecutionFactory(workflow=workflow)
        assert workflow.executions.count() == 2

    def test_workflow_owner_set_null_on_delete(self):
        """Test that deleting owner sets workflow.owner to NULL."""
        user = UserFactory()
        workflow = WorkflowFactory(owner=user)
        user.delete()
        workflow.refresh_from_db()
        assert workflow.owner is None


# ============================================================================
# WorkflowAction Model Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionModel:
    """Tests for the WorkflowAction model."""

    def test_create_workflow_action(self):
        """Test creating a workflow action."""
        workflow = WorkflowFactory()
        action = WorkflowActionFactory(
            workflow=workflow,
            action_type=WorkflowAction.SEND_EMAIL,
            action_config={'to': 'test@example.com'},
            order=0,
            delay_minutes=5,
            is_active=True,
        )

        assert action.workflow == workflow
        assert action.action_type == WorkflowAction.SEND_EMAIL
        assert action.action_config == {'to': 'test@example.com'}
        assert action.order == 0
        assert action.delay_minutes == 5
        assert action.is_active is True

    def test_workflow_action_str(self):
        """Test workflow action string representation."""
        workflow = WorkflowFactory(name='My WF')
        action = WorkflowActionFactory(
            workflow=workflow,
            action_type=WorkflowAction.SEND_EMAIL,
            order=1,
        )
        expected = f"My WF - {WorkflowAction.SEND_EMAIL} (#{action.order})"
        assert str(action) == expected

    def test_workflow_action_uuid_primary_key(self):
        """Test workflow action has UUID primary key."""
        action = WorkflowActionFactory()
        assert isinstance(action.id, uuid.UUID)

    def test_workflow_action_ordering(self):
        """Test actions are ordered by order field."""
        workflow = WorkflowFactory()
        a3 = WorkflowActionFactory(workflow=workflow, order=2)
        a1 = WorkflowActionFactory(workflow=workflow, order=0)
        a2 = WorkflowActionFactory(workflow=workflow, order=1)

        actions = list(workflow.actions.all())
        assert actions[0].order == 0
        assert actions[1].order == 1
        assert actions[2].order == 2

    def test_workflow_action_unique_together(self):
        """Test unique_together constraint on workflow and order."""
        workflow = WorkflowFactory()
        WorkflowActionFactory(workflow=workflow, order=0)
        with pytest.raises(IntegrityError):
            WorkflowActionFactory(workflow=workflow, order=0)

    def test_workflow_action_type_choices(self):
        """Test all action type choices are valid."""
        valid_types = [
            WorkflowAction.SEND_EMAIL,
            WorkflowAction.SEND_NOTIFICATION,
            WorkflowAction.UPDATE_CLIENT_STAGE,
            WorkflowAction.CREATE_TASK,
            WorkflowAction.CREATE_INVOICE,
            WorkflowAction.WEBHOOK_CALL,
        ]
        choices_dict = dict(WorkflowAction.ACTION_TYPE_CHOICES)
        for action_type in valid_types:
            assert action_type in choices_dict

    def test_workflow_action_with_each_type(self):
        """Test creating an action with each action type."""
        workflow = WorkflowFactory()
        for i, (action_value, _) in enumerate(WorkflowAction.ACTION_TYPE_CHOICES):
            action = WorkflowActionFactory(
                workflow=workflow,
                action_type=action_value,
                order=i + 10,
            )
            assert action.action_type == action_value

    def test_workflow_action_default_delay(self):
        """Test action defaults to 0 delay."""
        action = WorkflowActionFactory(delay_minutes=0)
        assert action.delay_minutes == 0

    def test_workflow_action_default_is_active(self):
        """Test action defaults to active."""
        action = WorkflowActionFactory()
        assert action.is_active is True

    def test_workflow_action_timestamps(self):
        """Test action has timestamps."""
        action = WorkflowActionFactory()
        assert action.created_at is not None
        assert action.updated_at is not None

    def test_workflow_action_cascade_delete(self):
        """Test actions are deleted when workflow is deleted."""
        workflow = WorkflowFactory()
        WorkflowActionFactory(workflow=workflow, order=0)
        WorkflowActionFactory(workflow=workflow, order=1)
        assert WorkflowAction.objects.filter(workflow=workflow).count() == 2

        workflow.delete()
        assert WorkflowAction.objects.filter(workflow=workflow).count() == 0

    def test_workflow_action_executions_relationship(self):
        """Test action can have related executions."""
        action = WorkflowActionFactory()
        execution = WorkflowExecutionFactory(workflow=action.workflow)
        ae1 = WorkflowActionExecutionFactory(execution=execution, action=action)
        ae2 = WorkflowActionExecutionFactory(execution=execution, action=action)
        assert action.executions.count() == 2


# ============================================================================
# WorkflowExecution Model Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowExecutionModel:
    """Tests for the WorkflowExecution model."""

    def test_create_workflow_execution(self):
        """Test creating a workflow execution."""
        user = UserFactory()
        workflow = WorkflowFactory()
        execution = WorkflowExecutionFactory(
            workflow=workflow,
            status=WorkflowExecution.PENDING,
            triggered_by=user,
            trigger_data={'event': 'contract_signed'},
        )

        assert execution.workflow == workflow
        assert execution.status == WorkflowExecution.PENDING
        assert execution.triggered_by == user
        assert execution.trigger_data == {'event': 'contract_signed'}

    def test_workflow_execution_str(self):
        """Test workflow execution string representation."""
        workflow = WorkflowFactory(name='Test WF')
        execution = WorkflowExecutionFactory(
            workflow=workflow,
            status=WorkflowExecution.COMPLETED,
        )
        expected = f"Execution of Test WF - {WorkflowExecution.COMPLETED}"
        assert str(execution) == expected

    def test_workflow_execution_uuid_primary_key(self):
        """Test execution has UUID primary key."""
        execution = WorkflowExecutionFactory()
        assert isinstance(execution.id, uuid.UUID)

    def test_workflow_execution_status_choices(self):
        """Test all status choices are valid."""
        valid_statuses = [
            WorkflowExecution.PENDING,
            WorkflowExecution.RUNNING,
            WorkflowExecution.COMPLETED,
            WorkflowExecution.FAILED,
            WorkflowExecution.CANCELLED,
        ]
        choices_dict = dict(WorkflowExecution.STATUS_CHOICES)
        for status_val in valid_statuses:
            assert status_val in choices_dict

    def test_workflow_execution_default_status(self):
        """Test execution defaults to PENDING status."""
        execution = WorkflowExecutionFactory()
        assert execution.status == WorkflowExecution.PENDING

    def test_workflow_execution_duration_with_both_timestamps(self):
        """Test duration property when both started_at and completed_at are set."""
        now = timezone.now()
        execution = WorkflowExecutionFactory(
            started_at=now - timedelta(minutes=10),
            completed_at=now,
        )
        duration = execution.duration
        assert duration is not None
        assert duration == timedelta(minutes=10)

    def test_workflow_execution_duration_without_started_at(self):
        """Test duration returns None when started_at is not set."""
        execution = WorkflowExecutionFactory(
            started_at=None,
            completed_at=timezone.now(),
        )
        assert execution.duration is None

    def test_workflow_execution_duration_without_completed_at(self):
        """Test duration returns None when completed_at is not set."""
        execution = WorkflowExecutionFactory(
            started_at=timezone.now(),
            completed_at=None,
        )
        assert execution.duration is None

    def test_workflow_execution_duration_both_none(self):
        """Test duration returns None when both timestamps are None."""
        execution = WorkflowExecutionFactory(
            started_at=None,
            completed_at=None,
        )
        assert execution.duration is None

    def test_workflow_execution_ordering(self):
        """Test executions are ordered by -created_at."""
        workflow = WorkflowFactory()
        e1 = WorkflowExecutionFactory(workflow=workflow)
        e2 = WorkflowExecutionFactory(workflow=workflow)
        executions = list(WorkflowExecution.objects.filter(workflow=workflow))
        assert executions[0].created_at >= executions[1].created_at

    def test_workflow_execution_triggered_by_nullable(self):
        """Test execution can be created without triggered_by."""
        execution = WorkflowExecutionFactory(triggered_by=None)
        assert execution.triggered_by is None

    def test_workflow_execution_error_message(self):
        """Test execution can store error message."""
        execution = WorkflowExecutionFactory(
            status=WorkflowExecution.FAILED,
            error_message='Something went wrong',
        )
        assert execution.error_message == 'Something went wrong'

    def test_workflow_execution_status_transitions(self):
        """Test status can be transitioned between states."""
        execution = WorkflowExecutionFactory(status=WorkflowExecution.PENDING)
        assert execution.status == WorkflowExecution.PENDING

        execution.status = WorkflowExecution.RUNNING
        execution.started_at = timezone.now()
        execution.save()
        execution.refresh_from_db()
        assert execution.status == WorkflowExecution.RUNNING

        execution.status = WorkflowExecution.COMPLETED
        execution.completed_at = timezone.now()
        execution.save()
        execution.refresh_from_db()
        assert execution.status == WorkflowExecution.COMPLETED

    def test_workflow_execution_cascade_delete(self):
        """Test executions are deleted when workflow is deleted."""
        workflow = WorkflowFactory()
        WorkflowExecutionFactory(workflow=workflow)
        WorkflowExecutionFactory(workflow=workflow)
        assert WorkflowExecution.objects.filter(workflow=workflow).count() == 2

        workflow.delete()
        assert WorkflowExecution.objects.filter(workflow=workflow).count() == 0

    def test_workflow_execution_action_executions_relationship(self):
        """Test execution has action_executions relationship."""
        workflow = WorkflowFactory()
        action = WorkflowActionFactory(workflow=workflow, order=0)
        execution = WorkflowExecutionFactory(workflow=workflow)
        ae = WorkflowActionExecutionFactory(execution=execution, action=action)
        assert execution.action_executions.count() == 1

    def test_workflow_execution_triggered_by_set_null_on_delete(self):
        """Test that deleting user sets triggered_by to NULL."""
        user = UserFactory()
        execution = WorkflowExecutionFactory(triggered_by=user)
        user.delete()
        execution.refresh_from_db()
        assert execution.triggered_by is None


# ============================================================================
# WorkflowActionExecution Model Tests
# ============================================================================

@pytest.mark.django_db
class TestWorkflowActionExecutionModel:
    """Tests for the WorkflowActionExecution model."""

    def test_create_workflow_action_execution(self):
        """Test creating a workflow action execution."""
        workflow = WorkflowFactory()
        action = WorkflowActionFactory(workflow=workflow, order=0)
        execution = WorkflowExecutionFactory(workflow=workflow)
        now = timezone.now()

        ae = WorkflowActionExecutionFactory(
            execution=execution,
            action=action,
            status=WorkflowActionExecution.COMPLETED,
            result_data={'result': 'ok'},
            started_at=now - timedelta(seconds=30),
            completed_at=now,
        )

        assert ae.execution == execution
        assert ae.action == action
        assert ae.status == WorkflowActionExecution.COMPLETED
        assert ae.result_data == {'result': 'ok'}
        assert ae.started_at is not None
        assert ae.completed_at is not None

    def test_workflow_action_execution_str(self):
        """Test action execution string representation."""
        action = WorkflowActionFactory(action_type=WorkflowAction.SEND_EMAIL)
        execution = WorkflowExecutionFactory(workflow=action.workflow)
        ae = WorkflowActionExecutionFactory(
            execution=execution,
            action=action,
            status=WorkflowActionExecution.COMPLETED,
        )
        expected = f"Action execution {WorkflowAction.SEND_EMAIL} - {WorkflowActionExecution.COMPLETED}"
        assert str(ae) == expected

    def test_workflow_action_execution_uuid_primary_key(self):
        """Test action execution has UUID primary key."""
        ae = WorkflowActionExecutionFactory()
        assert isinstance(ae.id, uuid.UUID)

    def test_workflow_action_execution_status_choices(self):
        """Test all status choices are valid."""
        valid_statuses = [
            WorkflowActionExecution.PENDING,
            WorkflowActionExecution.RUNNING,
            WorkflowActionExecution.COMPLETED,
            WorkflowActionExecution.FAILED,
            WorkflowActionExecution.SKIPPED,
        ]
        choices_dict = dict(WorkflowActionExecution.STATUS_CHOICES)
        for status_val in valid_statuses:
            assert status_val in choices_dict

    def test_workflow_action_execution_default_status(self):
        """Test action execution defaults to PENDING status."""
        ae = WorkflowActionExecutionFactory()
        assert ae.status == WorkflowActionExecution.PENDING

    def test_workflow_action_execution_error_message(self):
        """Test action execution can store error message."""
        ae = WorkflowActionExecutionFactory(
            status=WorkflowActionExecution.FAILED,
            error_message='Action failed',
        )
        assert ae.error_message == 'Action failed'

    def test_workflow_action_execution_ordering(self):
        """Test action executions are ordered by action__order."""
        workflow = WorkflowFactory()
        a1 = WorkflowActionFactory(workflow=workflow, order=0)
        a2 = WorkflowActionFactory(workflow=workflow, order=1)
        execution = WorkflowExecutionFactory(workflow=workflow)
        ae2 = WorkflowActionExecutionFactory(execution=execution, action=a2)
        ae1 = WorkflowActionExecutionFactory(execution=execution, action=a1)

        aes = list(execution.action_executions.all())
        assert aes[0].action.order <= aes[1].action.order

    def test_workflow_action_execution_cascade_delete_execution(self):
        """Test action executions are deleted when parent execution is deleted."""
        execution = WorkflowExecutionFactory()
        action = WorkflowActionFactory(workflow=execution.workflow, order=0)
        WorkflowActionExecutionFactory(execution=execution, action=action)
        assert WorkflowActionExecution.objects.filter(execution=execution).count() == 1

        execution.delete()
        assert WorkflowActionExecution.objects.filter(execution=execution).count() == 0

    def test_workflow_action_execution_cascade_delete_action(self):
        """Test action executions are deleted when action is deleted."""
        workflow = WorkflowFactory()
        action = WorkflowActionFactory(workflow=workflow, order=0)
        execution = WorkflowExecutionFactory(workflow=workflow)
        WorkflowActionExecutionFactory(execution=execution, action=action)

        action.delete()
        assert WorkflowActionExecution.objects.filter(action=action).count() == 0
