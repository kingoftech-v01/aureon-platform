"""Subscription serializers for Aureon SaaS Platform."""

from rest_framework import serializers
from django.utils import timezone
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanListSerializer(serializers.ModelSerializer):
    """Minimal plan serializer for list views."""

    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'currency',
            'interval', 'stripe_price_id', 'features', 'is_active',
            'subscriber_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_subscriber_count(self, obj):
        return obj.subscriptions.filter(status='active').count()


class SubscriptionPlanDetailSerializer(SubscriptionPlanListSerializer):
    """Full plan serializer with active subscriptions summary."""

    revenue_monthly = serializers.SerializerMethodField()

    class Meta(SubscriptionPlanListSerializer.Meta):
        fields = SubscriptionPlanListSerializer.Meta.fields + ['revenue_monthly']

    def get_revenue_monthly(self, obj):
        active_count = obj.subscriptions.filter(status='active').count()
        if obj.interval == 'year':
            return float(obj.price * active_count / 12)
        return float(obj.price * active_count)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Full subscription serializer with nested plan."""

    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_price = serializers.DecimalField(
        source='plan.price', max_digits=10, decimal_places=2, read_only=True
    )
    plan_interval = serializers.CharField(source='plan.interval', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_active = serializers.ReadOnlyField()
    days_until_renewal = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_email', 'plan', 'plan_name', 'plan_price',
            'plan_interval', 'status', 'stripe_subscription_id',
            'current_period_start', 'current_period_end',
            'cancel_at_period_end', 'canceled_at', 'is_active',
            'days_until_renewal', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'status', 'stripe_subscription_id',
            'current_period_start', 'current_period_end',
            'cancel_at_period_end', 'canceled_at', 'created_at', 'updated_at',
        ]


class SubscriptionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new subscription."""

    plan_id = serializers.IntegerField()
    payment_method_id = serializers.CharField(
        required=False, allow_blank=True,
        help_text='Stripe payment method ID. Required for paid plans.'
    )

    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError('Plan not found or inactive.')
        return value

    def validate(self, data):
        user = self.context['request'].user
        active_sub = Subscription.objects.filter(
            user=user, status__in=['active', 'trialing']
        ).first()
        if active_sub:
            raise serializers.ValidationError({
                'plan_id': 'You already have an active subscription. '
                           'Use the change_plan endpoint to switch plans.'
            })
        return data


class SubscriptionChangePlanSerializer(serializers.Serializer):
    """Serializer for upgrading/downgrading a subscription."""

    new_plan_id = serializers.IntegerField()
    prorate = serializers.BooleanField(default=True)

    def validate_new_plan_id(self, value):
        try:
            SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError('Plan not found or inactive.')
        return value


class SubscriptionCancelSerializer(serializers.Serializer):
    """Serializer for cancellation options."""

    immediate = serializers.BooleanField(
        default=False,
        help_text='If true, cancel immediately. Otherwise cancel at period end.'
    )
    reason = serializers.CharField(
        required=False, allow_blank=True, max_length=500,
        help_text='Optional cancellation reason.'
    )


class SubscriptionStatsSerializer(serializers.Serializer):
    """Aggregated subscription statistics."""

    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    canceled_subscriptions = serializers.IntegerField()
    past_due_subscriptions = serializers.IntegerField()
    trialing_subscriptions = serializers.IntegerField()
    paused_subscriptions = serializers.IntegerField()
    monthly_recurring_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    annual_recurring_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_revenue_per_user = serializers.DecimalField(max_digits=12, decimal_places=2)
    churn_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
