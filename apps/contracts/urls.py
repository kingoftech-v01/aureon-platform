"""
URL configuration for contracts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, ContractMilestoneViewSet
from .views_frontend import (
    ContractListView,
    ContractDetailView,
    ContractCreateView,
    ContractEditView,
    ContractSignView,
    MilestoneListView,
)

app_name = 'contracts'

router = DefaultRouter()
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'milestones', ContractMilestoneViewSet, basename='contract-milestone')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', ContractListView.as_view(), name='contract_list'),
    path('create/', ContractCreateView.as_view(), name='contract_create'),
    path('<uuid:pk>/', ContractDetailView.as_view(), name='contract_detail'),
    path('<uuid:pk>/edit/', ContractEditView.as_view(), name='contract_edit'),
    path('<uuid:pk>/sign/', ContractSignView.as_view(), name='contract_sign'),
    path('milestones/', MilestoneListView.as_view(), name='milestone_list'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
