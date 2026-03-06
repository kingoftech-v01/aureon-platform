"""
Subscription Management Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'slug', 'description', 'price', 'currency', 'interval', 'stripe_price_id', 'features', 'is_active']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'plan_id', 'status', 'stripe_subscription_id',
                  'current_period_start', 'current_period_end', 'cancel_at_period_end',
                  'canceled_at', 'created_at', 'updated_at']
        read_only_fields = ['user', 'stripe_subscription_id', 'current_period_start',
                           'current_period_end', 'canceled_at']


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = SubscriptionPlan.objects.filter(is_active=True)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        subscription.cancel_at_period_end = True
        subscription.status = 'canceled'
        subscription.save()
        return Response(self.get_serializer(subscription).data)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        subscription = self.get_object()
        if subscription.cancel_at_period_end:
            subscription.cancel_at_period_end = False
            subscription.status = 'active'
            subscription.save()
            return Response(self.get_serializer(subscription).data)
        return Response({'error': 'Subscription is not scheduled for cancellation'},
                       status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def current(self, request):
        subscription = Subscription.objects.filter(
            user=request.user, status__in=['active', 'trialing']
        ).first()
        if subscription:
            return Response(self.get_serializer(subscription).data)
        return Response({'detail': 'No active subscription'}, status=status.HTTP_404_NOT_FOUND)
