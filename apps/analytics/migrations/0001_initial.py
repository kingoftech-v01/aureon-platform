# Generated manually for Aureon SaaS Platform

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0001_initial'),
        ('invoicing', '0001_initial'),
        ('payments', '0001_initial'),
        ('contracts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RevenueMetric',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('year', models.PositiveIntegerField(help_text='Year for this metric period', verbose_name='Year')),
                ('month', models.PositiveIntegerField(help_text='Month (1-12) for this metric period', verbose_name='Month')),
                ('total_revenue', models.DecimalField(decimal_places=2, default=0, help_text='Total revenue for this period', max_digits=12, verbose_name='Total Revenue')),
                ('recurring_revenue', models.DecimalField(decimal_places=2, default=0, help_text='Monthly recurring revenue (MRR)', max_digits=12, verbose_name='Recurring Revenue')),
                ('one_time_revenue', models.DecimalField(decimal_places=2, default=0, help_text='One-time project revenue', max_digits=12, verbose_name='One-Time Revenue')),
                ('invoices_sent', models.PositiveIntegerField(default=0, help_text='Number of invoices sent', verbose_name='Invoices Sent')),
                ('invoices_paid', models.PositiveIntegerField(default=0, help_text='Number of invoices paid', verbose_name='Invoices Paid')),
                ('average_invoice_value', models.DecimalField(decimal_places=2, default=0, help_text='Average invoice amount', max_digits=12, verbose_name='Average Invoice Value')),
                ('payment_success_rate', models.DecimalField(decimal_places=2, default=0, help_text='Percentage of successful payments', max_digits=5, verbose_name='Payment Success Rate')),
                ('new_clients', models.PositiveIntegerField(default=0, help_text='New clients acquired this period', verbose_name='New Clients')),
                ('active_clients', models.PositiveIntegerField(default=0, help_text='Total active clients', verbose_name='Active Clients')),
                ('churned_clients', models.PositiveIntegerField(default=0, help_text='Clients lost this period', verbose_name='Churned Clients')),
                ('churn_rate', models.DecimalField(decimal_places=2, default=0, help_text='Client churn rate percentage', max_digits=5, verbose_name='Churn Rate')),
                ('outstanding_balance', models.DecimalField(decimal_places=2, default=0, help_text='Total outstanding receivables', max_digits=12, verbose_name='Outstanding Balance')),
                ('overdue_amount', models.DecimalField(decimal_places=2, default=0, help_text='Total overdue amount', max_digits=12, verbose_name='Overdue Amount')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Revenue Metric',
                'verbose_name_plural': 'Revenue Metrics',
                'ordering': ['-year', '-month'],
                'unique_together': {('year', 'month')},
            },
        ),
        migrations.CreateModel(
            name='ClientMetric',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('lifetime_value', models.DecimalField(decimal_places=2, default=0, help_text='Total revenue from this client', max_digits=12, verbose_name='Lifetime Value')),
                ('total_invoices', models.PositiveIntegerField(default=0, help_text='Total number of invoices', verbose_name='Total Invoices')),
                ('paid_invoices', models.PositiveIntegerField(default=0, help_text='Number of paid invoices', verbose_name='Paid Invoices')),
                ('overdue_invoices', models.PositiveIntegerField(default=0, help_text='Number of overdue invoices', verbose_name='Overdue Invoices')),
                ('total_payments', models.PositiveIntegerField(default=0, help_text='Total number of payments', verbose_name='Total Payments')),
                ('failed_payments', models.PositiveIntegerField(default=0, help_text='Number of failed payments', verbose_name='Failed Payments')),
                ('outstanding_balance', models.DecimalField(decimal_places=2, default=0, help_text='Current outstanding balance', max_digits=12, verbose_name='Outstanding Balance')),
                ('payment_reliability_score', models.DecimalField(decimal_places=2, default=0, help_text='Payment reliability score (0-100)', max_digits=5, verbose_name='Payment Reliability Score')),
                ('average_days_to_pay', models.PositiveIntegerField(default=0, help_text='Average days to pay invoices', verbose_name='Average Days to Pay')),
                ('last_payment_date', models.DateField(blank=True, help_text='Date of most recent payment', null=True, verbose_name='Last Payment Date')),
                ('days_since_last_payment', models.PositiveIntegerField(default=0, help_text='Days since last payment', verbose_name='Days Since Last Payment')),
                ('total_contracts', models.PositiveIntegerField(default=0, help_text='Total number of contracts', verbose_name='Total Contracts')),
                ('active_contracts', models.PositiveIntegerField(default=0, help_text='Number of active contracts', verbose_name='Active Contracts')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('client', models.OneToOneField(help_text='Client these metrics belong to', on_delete=django.db.models.deletion.CASCADE, to='clients.client', verbose_name='Client')),
            ],
            options={
                'verbose_name': 'Client Metric',
                'verbose_name_plural': 'Client Metrics',
                'ordering': ['-lifetime_value'],
            },
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('activity_type', models.CharField(choices=[('invoice_created', 'Invoice Created'), ('invoice_sent', 'Invoice Sent'), ('invoice_paid', 'Invoice Paid'), ('payment_received', 'Payment Received'), ('payment_failed', 'Payment Failed'), ('contract_created', 'Contract Created'), ('contract_signed', 'Contract Signed'), ('client_created', 'Client Created'), ('user_login', 'User Login'), ('settings_changed', 'Settings Changed'), ('export_generated', 'Export Generated'), ('webhook_sent', 'Webhook Sent')], help_text='Type of activity', max_length=50, verbose_name='Activity Type')),
                ('description', models.CharField(help_text='Human-readable description', max_length=500, verbose_name='Description')),
                ('related_object_type', models.CharField(blank=True, help_text='Type of related object (e.g., Invoice, Payment)', max_length=100, verbose_name='Related Object Type')),
                ('related_object_id', models.CharField(blank=True, help_text='ID of related object', max_length=100, verbose_name='Related Object ID')),
                ('related_objects', models.JSONField(default=dict, help_text='Map of related object types to IDs', verbose_name='Related Objects')),
                ('metadata', models.JSONField(default=dict, help_text='Additional activity metadata', verbose_name='Metadata')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of user', null=True, verbose_name='IP Address')),
                ('user_agent', models.CharField(blank=True, help_text='User agent string', max_length=500, verbose_name='User Agent')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('user', models.ForeignKey(blank=True, help_text='User who performed this activity', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Activity Log',
                'verbose_name_plural': 'Activity Logs',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['activity_type'], name='analytics_a_activit_idx'),
                    models.Index(fields=['created_at'], name='analytics_a_created_idx'),
                ],
            },
        ),
    ]
