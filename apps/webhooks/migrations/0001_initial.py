# Generated manually for Aureon SaaS Platform

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookEndpoint',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Descriptive name for this endpoint', max_length=255, verbose_name='Endpoint Name')),
                ('url', models.URLField(help_text='Full URL where webhooks will be sent', max_length=500, verbose_name='Webhook URL')),
                ('secret_key', models.CharField(help_text='Secret key for HMAC signature verification', max_length=255, verbose_name='Secret Key')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this endpoint is currently active', verbose_name='Active')),
                ('event_types', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), default=list, help_text='List of event types this endpoint subscribes to', size=None, verbose_name='Event Types')),
                ('total_deliveries', models.PositiveIntegerField(default=0, help_text='Total number of delivery attempts', verbose_name='Total Deliveries')),
                ('successful_deliveries', models.PositiveIntegerField(default=0, help_text='Number of successful deliveries', verbose_name='Successful Deliveries')),
                ('failed_deliveries', models.PositiveIntegerField(default=0, help_text='Number of failed deliveries', verbose_name='Failed Deliveries')),
                ('last_delivery_at', models.DateTimeField(blank=True, help_text='Timestamp of last delivery attempt', null=True, verbose_name='Last Delivery At')),
                ('last_delivery_status', models.CharField(blank=True, help_text='Status of last delivery attempt', max_length=20, verbose_name='Last Delivery Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Webhook Endpoint',
                'verbose_name_plural': 'Webhook Endpoints',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.CharField(choices=[('stripe', 'Stripe'), ('custom', 'Custom')], help_text='Source system that generated this webhook', max_length=50, verbose_name='Source')),
                ('event_type', models.CharField(help_text='Type of event (e.g., payment_intent.succeeded)', max_length=255, verbose_name='Event Type')),
                ('event_id', models.CharField(help_text='Unique ID from the source system', max_length=255, unique=True, verbose_name='Event ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('processed', 'Processed'), ('failed', 'Failed')], default='pending', help_text='Current processing status', max_length=20, verbose_name='Status')),
                ('payload', models.JSONField(help_text='Full webhook payload data', verbose_name='Payload Data')),
                ('response_data', models.JSONField(blank=True, help_text='Response data from processing', null=True, verbose_name='Response Data')),
                ('error_message', models.TextField(blank=True, help_text='Error message if processing failed', verbose_name='Error Message')),
                ('retry_count', models.PositiveIntegerField(default=0, help_text='Number of retry attempts', verbose_name='Retry Count')),
                ('max_retries', models.PositiveIntegerField(default=3, help_text='Maximum number of retry attempts', verbose_name='Max Retries')),
                ('next_retry_at', models.DateTimeField(blank=True, help_text='Scheduled time for next retry', null=True, verbose_name='Next Retry At')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of webhook source', null=True, verbose_name='IP Address')),
                ('user_agent', models.CharField(blank=True, help_text='User agent of webhook request', max_length=500, verbose_name='User Agent')),
                ('received_at', models.DateTimeField(auto_now_add=True, verbose_name='Received At')),
                ('processed_at', models.DateTimeField(blank=True, help_text='When the event was successfully processed', null=True, verbose_name='Processed At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Webhook Event',
                'verbose_name_plural': 'Webhook Events',
                'ordering': ['-received_at'],
                'indexes': [
                    models.Index(fields=['event_type'], name='webhooks_we_event_t_idx'),
                    models.Index(fields=['status'], name='webhooks_we_status_idx'),
                    models.Index(fields=['source'], name='webhooks_we_source_idx'),
                ],
            },
        ),
    ]
