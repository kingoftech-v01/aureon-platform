"""
URL configuration for contracts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, ContractMilestoneViewSet

app_name = 'contracts'

router = DefaultRouter()
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'milestones', ContractMilestoneViewSet, basename='contract-milestone')

urlpatterns = [
    path('', include(router.urls)),
]
