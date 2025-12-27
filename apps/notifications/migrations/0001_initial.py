# Generated manually for Aureon SaaS Platform

import django.contrib.postgres.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('invoicing', '0001_initial'),
        ('payments', '0001_initial'),
        ('contracts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Descriptive name for this template', max_length=255, verbose_name='Template Name')),
                ('template_type', models.CharField(choices=[('invoice_created', 'Invoice Created'), ('invoice_sent', 'Invoice Sent to Client'), ('invoice_paid', 'Invoice Paid'), ('invoice_overdue', 'Invoice Overdue'), ('payment_received', 'Payment Received'), ('payment_failed', 'Payment Failed'), ('payment_receipt', 'Payment Receipt'), ('contract_signed', 'Contract Signed'), ('contract_expiring', 'Contract Expiring Soon'), ('client_welcome', 'New Client Welcome'), ('reminder_payment_due', 'Payment Due Reminder')], help_text='Type of notification this template is for', max_length=50, unique=True, verbose_name='Template Type')),
                ('channel', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('in_app', 'In-App Notification')], default='email', help_text='Communication channel for this notification', max_length=20, verbose_name='Channel')),
                ('subject', models.CharField(blank=True, help_text='Subject line for email notifications. Supports {{variables}}', max_length=255, verbose_name='Email Subject')),
                ('body_text', models.TextField(help_text='Plain text version of the message. Supports {{variables}}', verbose_name='Plain Text Body')),
                ('body_html', models.TextField(blank=True, help_text='HTML version of the message. Supports {{variables}}', verbose_name='HTML Body')),
                ('send_to_client', models.BooleanField(default=True, help_text='Whether to send this notification to clients', verbose_name='Send to Client')),
                ('send_to_owner', models.BooleanField(default=False, help_text='Whether to send this notification to business owner', verbose_name='Send to Owner')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this template is currently active', verbose_name='Active')),
                ('available_variables', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), default=list, help_text='List of available template variables', size=None, verbose_name='Available Variables')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Notification Template',
                'verbose_name_plural': 'Notification Templates',
                'ordering': ['template_type'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('recipient_type', models.CharField(choices=[('client', 'Client'), ('owner', 'Business Owner'), ('custom', 'Custom Email')], help_text='Type of recipient', max_length=20, verbose_name='Recipient Type')),
                ('email', models.EmailField(blank=True, help_text='Email address if custom recipient', max_length=254, verbose_name='Email Address')),
                ('subject', models.CharField(help_text='Email subject line', max_length=500, verbose_name='Subject')),
                ('message_text', models.TextField(help_text='Plain text message content', verbose_name='Message Text')),
                ('message_html', models.TextField(blank=True, help_text='HTML message content', verbose_name='Message HTML')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('bounced', 'Bounced')], default='pending', help_text='Current delivery status', max_length=20, verbose_name='Status')),
                ('sent_at', models.DateTimeField(blank=True, help_text='When the notification was sent', null=True, verbose_name='Sent At')),
                ('delivered_at', models.DateTimeField(blank=True, help_text='When the notification was delivered', null=True, verbose_name='Delivered At')),
                ('error_message', models.TextField(blank=True, help_text='Error message if delivery failed', verbose_name='Error Message')),
                ('retry_count', models.PositiveIntegerField(default=0, help_text='Number of retry attempts', verbose_name='Retry Count')),
                ('max_retries', models.PositiveIntegerField(default=3, help_text='Maximum number of retry attempts', verbose_name='Max Retries')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata', verbose_name='Metadata')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('user', models.ForeignKey(blank=True, help_text='User who should receive this notification', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('template', models.ForeignKey(blank=True, help_text='Template used for this notification', null=True, on_delete=django.db.models.deletion.SET_NULL, to='notifications.notificationtemplate', verbose_name='Template')),
                ('related_invoice', models.ForeignKey(blank=True, help_text='Related invoice if applicable', null=True, on_delete=django.db.models.deletion.CASCADE, to='invoicing.invoice', verbose_name='Related Invoice')),
                ('related_payment', models.ForeignKey(blank=True, help_text='Related payment if applicable', null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.payment', verbose_name='Related Payment')),
                ('related_contract', models.ForeignKey(blank=True, help_text='Related contract if applicable', null=True, on_delete=django.db.models.deletion.CASCADE, to='contracts.contract', verbose_name='Related Contract')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['status'], name='notificatio_status_idx'),
                    models.Index(fields=['created_at'], name='notificatio_created_idx'),
                ],
            },
        ),
    ]
