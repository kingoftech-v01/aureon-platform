"""
URL configuration for tasks app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskCommentViewSet
from .views_frontend import (
    TaskListView,
    TaskDetailView,
    TaskCreateView,
    TaskBoardView,
)

app_name = 'tasks'

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-comments', TaskCommentViewSet, basename='task-comment')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', TaskListView.as_view(), name='task_list'),
    path('create/', TaskCreateView.as_view(), name='task_create'),
    path('board/', TaskBoardView.as_view(), name='task_board'),
    path('<uuid:pk>/', TaskDetailView.as_view(), name='task_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
