"""
Views and ViewSets for the workflows app API.
"""

from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Workflow,
    WorkflowAction,
    WorkflowExecution,
)
from .serializers import (
    WorkflowListSerializer,
    WorkflowDetailSerializer,
    WorkflowCreateUpdateSerializer,
    WorkflowActionSerializer,
    WorkflowExecutionSerializer,
)
from .filters import WorkflowFilter


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workflow CRUD operations.

    list: Get list of workflows with filtering and search
    retrieve: Get workflow details with actions
    create: Create a new workflow
    update: Update a workflow
    partial_update: Partially update a workflow
    destroy: Delete a workflow
    """

    queryset = Workflow.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WorkflowFilter
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WorkflowListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return WorkflowCreateUpdateSerializer
        return WorkflowDetailSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a workflow.

        Sets is_active to True.
        """
        workflow = self.get_object()
        workflow.is_active = True
        workflow.save(update_fields=['is_active', 'updated_at'])
        serializer = WorkflowDetailSerializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a workflow.

        Sets is_active to False.
        """
        workflow = self.get_object()
        workflow.is_active = False
        workflow.save(update_fields=['is_active', 'updated_at'])
        serializer = WorkflowDetailSerializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Manually execute a workflow.

        Creates a new WorkflowExecution with status=PENDING.
        """
        workflow = self.get_object()
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status=WorkflowExecution.PENDING,
            triggered_by=request.user,
            trigger_data=request.data.get('trigger_data', {}),
        )
        serializer = WorkflowExecutionSerializer(execution)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Get all executions for a workflow.
        """
        workflow = self.get_object()
        executions = workflow.executions.all()
        serializer = WorkflowExecutionSerializer(
            executions, many=True, context={'request': request}
        )
        return Response(serializer.data)


class WorkflowActionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WorkflowAction CRUD operations.
    """

    queryset = WorkflowAction.objects.all()
    serializer_class = WorkflowActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow', 'action_type', 'is_active']
    ordering = ['order']


class WorkflowExecutionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for WorkflowExecution read operations.

    list: Get list of workflow executions
    retrieve: Get execution details with action executions
    """

    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['workflow', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
