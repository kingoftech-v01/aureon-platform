from django.contrib import admin
from .models import SubscriptionPlan, Subscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'currency', 'interval', 'is_active', 'created_at']
    list_filter = ['is_active', 'interval', 'currency']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['price']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_end', 'cancel_at_period_end', 'created_at']
    list_filter = ['status', 'plan', 'cancel_at_period_end']
    search_fields = ['user__email', 'stripe_subscription_id']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
