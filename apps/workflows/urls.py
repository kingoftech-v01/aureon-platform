"""
URL configuration for workflows app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet, WorkflowActionViewSet, WorkflowExecutionViewSet
from .views_frontend import (
    WorkflowListView,
    WorkflowDetailView,
    WorkflowCreateView,
    WorkflowEditView,
    WorkflowExecutionListView,
)

app_name = 'workflows'

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-actions', WorkflowActionViewSet, basename='workflow-action')
router.register(r'workflow-executions', WorkflowExecutionViewSet, basename='workflow-execution')

api_urlpatterns = [
    path('', include(router.urls)),
]

frontend_urlpatterns = [
    path('', WorkflowListView.as_view(), name='workflow_list'),
    path('create/', WorkflowCreateView.as_view(), name='workflow_create'),
    path('<uuid:pk>/', WorkflowDetailView.as_view(), name='workflow_detail'),
    path('<uuid:pk>/edit/', WorkflowEditView.as_view(), name='workflow_edit'),
    path('executions/', WorkflowExecutionListView.as_view(), name='execution_list'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
