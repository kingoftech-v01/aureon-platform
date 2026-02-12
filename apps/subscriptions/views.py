"""Subscription REST API views for Aureon SaaS Platform."""

import logging
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import SubscriptionPlan, Subscription
from .serializers import (
    SubscriptionPlanListSerializer,
    SubscriptionPlanDetailSerializer,
    SubscriptionSerializer,
    SubscriptionCreateSerializer,
    SubscriptionChangePlanSerializer,
    SubscriptionCancelSerializer,
    SubscriptionStatsSerializer,
)
from .services import SubscriptionService

logger = logging.getLogger(__name__)


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for subscription plans.

    list:   GET  /api/subscriptions/plans/         — list active plans
    create: POST /api/subscriptions/plans/         — create a plan (admin)
    read:   GET  /api/subscriptions/plans/{id}/    — plan detail
    update: PUT  /api/subscriptions/plans/{id}/    — update plan (admin)
    delete: DEL  /api/subscriptions/plans/{id}/    — deactivate plan (admin)
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'interval', 'currency']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at']
    ordering = ['price']

    def get_queryset(self):
        qs = SubscriptionPlan.objects.all()
        # Non-staff users only see active plans
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubscriptionPlanDetailSerializer
        return SubscriptionPlanListSerializer

    def perform_destroy(self, instance):
        """Soft-delete: deactivate instead of deleting."""
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])


class SubscriptionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for user subscriptions.

    list:        GET  /api/subscriptions/                — user's subscriptions
    retrieve:    GET  /api/subscriptions/{id}/           — subscription detail
    subscribe:   POST /api/subscriptions/subscribe/      — create subscription
    cancel:      POST /api/subscriptions/{id}/cancel/    — cancel subscription
    pause:       POST /api/subscriptions/{id}/pause/     — pause subscription
    resume:      POST /api/subscriptions/{id}/resume/    — resume subscription
    change_plan: POST /api/subscriptions/{id}/change_plan/ — upgrade/downgrade
    current:     GET  /api/subscriptions/current/        — active subscription
    stats:       GET  /api/subscriptions/stats/          — subscription metrics (admin)
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'plan']
    ordering_fields = ['created_at', 'current_period_end']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Subscription.objects.select_related('plan', 'user').all()
        return Subscription.objects.select_related('plan', 'user').filter(user=user)

    # ------------------------------------------------------------------
    # Custom actions
    # ------------------------------------------------------------------

    @action(detail=False, methods=['post'], serializer_class=SubscriptionCreateSerializer)
    def subscribe(self, request):
        """Create a new subscription for the authenticated user."""
        serializer = SubscriptionCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            subscription = SubscriptionService.create_subscription(
                user=request.user,
                plan_id=serializer.validated_data['plan_id'],
                payment_method_id=serializer.validated_data.get('payment_method_id'),
            )
        except Exception as e:
            logger.exception("Subscription creation failed")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            SubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], serializer_class=SubscriptionCancelSerializer)
    def cancel(self, request, pk=None):
        """Cancel a subscription."""
        subscription = self.get_object()
        serializer = SubscriptionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated = SubscriptionService.cancel_subscription(
                subscription_id=subscription.id,
                immediate=serializer.validated_data.get('immediate', False),
                reason=serializer.validated_data.get('reason', ''),
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(updated).data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a subscription."""
        subscription = self.get_object()

        try:
            updated = SubscriptionService.pause_subscription(subscription.id)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(updated).data)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused subscription."""
        subscription = self.get_object()

        try:
            updated = SubscriptionService.resume_subscription(subscription.id)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(updated).data)

    @action(
        detail=True, methods=['post'],
        serializer_class=SubscriptionChangePlanSerializer,
    )
    def change_plan(self, request, pk=None):
        """Upgrade or downgrade the subscription plan."""
        subscription = self.get_object()
        serializer = SubscriptionChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated = SubscriptionService.change_plan(
                subscription_id=subscription.id,
                new_plan_id=serializer.validated_data['new_plan_id'],
                prorate=serializer.validated_data.get('prorate', True),
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SubscriptionSerializer(updated).data)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the user's current active subscription."""
        subscription = Subscription.objects.select_related('plan', 'user').filter(
            user=request.user,
            status__in=['active', 'trialing'],
        ).first()

        if not subscription:
            return Response(
                {'detail': 'No active subscription found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(SubscriptionSerializer(subscription).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Subscription metrics (staff only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Admin access required.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = SubscriptionService.get_stats()
        serializer = SubscriptionStatsSerializer(data)
        return Response(serializer.data)
