"""
Serializers for the tasks app.
"""

from rest_framework import serializers
from .models import Task, TaskComment


class TaskCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = '__all__'
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        """Get author full name."""
        if obj.author:
            return obj.author.full_name or f"{obj.author.first_name} {obj.author.last_name}".strip()
        return None


class AssignedToNestedSerializer(serializers.Serializer):
    """
    Lightweight nested serializer for assigned user.
    """
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class ClientNestedSerializer(serializers.Serializer):
    """
    Lightweight nested serializer for client reference.
    """
    id = serializers.UUIDField(read_only=True)
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        """Get client display name."""
        return obj.get_display_name()


class TaskListSerializer(serializers.ModelSerializer):
    """
    Serializer for task list view (minimal fields for performance).
    """
    assigned_to = AssignedToNestedSerializer(read_only=True)
    client = ClientNestedSerializer(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'due_date',
            'assigned_to', 'client', 'created_at', 'is_overdue',
            'comments_count',
        ]
        read_only_fields = ['id', 'created_at']

    def get_comments_count(self, obj):
        """Return the number of comments on this task."""
        return obj.comments.count()


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for task detail view.
    """
    comments = TaskCommentSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_assigned_to_name(self, obj):
        """Get assigned user full name."""
        if obj.assigned_to:
            return obj.assigned_to.full_name or f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
        return None

    def get_created_by_name(self, obj):
        """Get creator full name."""
        if obj.created_by:
            return obj.created_by.full_name or f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None

    def get_client_name(self, obj):
        """Get client display name."""
        if obj.client:
            return obj.client.get_display_name()
        return None


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating tasks.
    """

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'due_date',
            'assigned_to', 'client', 'contract', 'invoice', 'tags',
        ]


class TaskStatsSerializer(serializers.Serializer):
    """
    Serializer for task statistics.
    """
    total = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())
    by_priority = serializers.DictField(child=serializers.IntegerField())
    overdue_count = serializers.IntegerField()
