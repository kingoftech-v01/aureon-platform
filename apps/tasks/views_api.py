"""
Views and ViewSets for the tasks app API.
"""

from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task, TaskComment
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
    TaskCommentSerializer,
    TaskStatsSerializer,
)
from .filters import TaskFilter


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations.

    list: Get list of tasks with filtering and search
    retrieve: Get task details with comments
    create: Create a new task
    update: Update a task
    partial_update: Partially update a task
    destroy: Delete a task
    """

    queryset = Task.objects.select_related(
        'assigned_to', 'created_by', 'client', 'contract', 'invoice'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer

    def perform_create(self, serializer):
        """Set created_by to current user on create."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark a task as done.

        Sets status to DONE and records completed_at timestamp.
        """
        task = self.get_object()

        if task.status == Task.DONE:
            return Response(
                {'detail': 'Task is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.status = Task.DONE
        task.completed_at = timezone.now()
        task.save()

        serializer = TaskDetailSerializer(task, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """
        Reopen a completed or cancelled task.

        Sets status back to TODO and clears completed_at.
        """
        task = self.get_object()

        task.status = Task.TODO
        task.completed_at = None
        task.save()

        serializer = TaskDetailSerializer(task, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get task statistics.

        Returns total tasks, counts by status, counts by priority, and overdue count.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Counts by status
        by_status = {}
        for choice_value, choice_label in Task.STATUS_CHOICES:
            by_status[choice_value] = queryset.filter(status=choice_value).count()

        # Counts by priority
        by_priority = {}
        for choice_value, choice_label in Task.PRIORITY_CHOICES:
            by_priority[choice_value] = queryset.filter(priority=choice_value).count()

        # Overdue count: not DONE/CANCELLED and due_date in the past
        overdue_count = queryset.exclude(
            status__in=[Task.DONE, Task.CANCELLED]
        ).filter(
            due_date__isnull=False,
            due_date__lt=timezone.now()
        ).count()

        stats = {
            'total': queryset.count(),
            'by_status': by_status,
            'by_priority': by_priority,
            'overdue_count': overdue_count,
        }

        serializer = TaskStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """
        Get all comments for a task.
        """
        task = self.get_object()
        comments = task.comments.select_related('author').all()
        serializer = TaskCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskComment CRUD operations.
    """

    queryset = TaskComment.objects.select_related('author', 'task')
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['task']
    ordering = ['created_at']

    def perform_create(self, serializer):
        """Set author to current user on create."""
        serializer.save(author=self.request.user)
