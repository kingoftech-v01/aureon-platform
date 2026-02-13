"""
Serializers for the workflows app.
"""

from rest_framework import serializers
from .models import (
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    WorkflowActionExecution,
)


class UUIDPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """PrimaryKeyRelatedField that serializes UUID primary keys as strings."""

    def to_representation(self, value):
        pk = super().to_representation(value)
        return str(pk)


class WorkflowActionSerializer(serializers.ModelSerializer):
    """
    Serializer for workflow actions.
    """
    workflow = UUIDPrimaryKeyRelatedField(queryset=Workflow.objects.all())

    class Meta:
        model = WorkflowAction
        fields = [
            'id', 'workflow', 'action_type', 'action_config',
            'order', 'delay_minutes', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowActionExecutionSerializer(serializers.ModelSerializer):
    """
    Serializer for workflow action executions.
    """
    execution = UUIDPrimaryKeyRelatedField(queryset=WorkflowExecution.objects.all())
    action = UUIDPrimaryKeyRelatedField(queryset=WorkflowAction.objects.all())

    class Meta:
        model = WorkflowActionExecution
        fields = [
            'id', 'execution', 'action', 'status',
            'result_data', 'started_at', 'completed_at',
            'error_message',
        ]
        read_only_fields = ['id']


class WorkflowListSerializer(serializers.ModelSerializer):
    """
    Serializer for workflow list view (minimal fields).
    """
    actions_count = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'trigger_type', 'is_active',
            'created_at', 'actions_count',
        ]
        read_only_fields = ['id', 'created_at']

    def get_actions_count(self, obj):
        """Get the number of actions in the workflow."""
        return obj.actions.count()


class WorkflowDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for workflow detail view.
    """
    actions = WorkflowActionSerializer(many=True, read_only=True)
    owner = UUIDPrimaryKeyRelatedField(
        queryset=Workflow.owner.field.related_model.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'is_active',
            'trigger_type', 'trigger_config', 'owner',
            'created_at', 'updated_at', 'actions',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating workflows.
    """

    class Meta:
        model = Workflow
        fields = [
            'name', 'description', 'trigger_type',
            'trigger_config', 'is_active',
        ]


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """
    Serializer for workflow executions.
    """
    action_executions = WorkflowActionExecutionSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    workflow = UUIDPrimaryKeyRelatedField(queryset=Workflow.objects.all())
    triggered_by = UUIDPrimaryKeyRelatedField(
        queryset=WorkflowExecution.triggered_by.field.related_model.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'workflow', 'status', 'triggered_by',
            'trigger_data', 'started_at', 'completed_at',
            'error_message', 'created_at', 'duration',
            'action_executions',
        ]
        read_only_fields = ['id', 'created_at']

    def get_duration(self, obj):
        """Get execution duration as a string."""
        duration = obj.duration
        if duration is not None:
            return str(duration)
        return None
