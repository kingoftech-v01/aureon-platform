"""
URL configuration for proposals app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProposalViewSet, ProposalSectionViewSet, ProposalPricingOptionViewSet
from .views_frontend import (
    ProposalListView,
    ProposalDetailView,
    ProposalCreateView,
    ProposalEditView,
    ProposalClientView,
)

app_name = 'proposals'

router = DefaultRouter()
router.register(r'proposals', ProposalViewSet, basename='proposal')
router.register(r'proposal-sections', ProposalSectionViewSet, basename='proposal-section')
router.register(r'proposal-pricing-options', ProposalPricingOptionViewSet, basename='proposal-pricing-option')

api_urlpatterns = [
    path('', include(router.urls)),
]

frontend_urlpatterns = [
    path('', ProposalListView.as_view(), name='proposal_list'),
    path('create/', ProposalCreateView.as_view(), name='proposal_create'),
    path('<uuid:pk>/', ProposalDetailView.as_view(), name='proposal_detail'),
    path('<uuid:pk>/edit/', ProposalEditView.as_view(), name='proposal_edit'),
    path('<uuid:pk>/view/', ProposalClientView.as_view(), name='proposal_client_view'),
]

urlpatterns = frontend_urlpatterns + api_urlpatterns
