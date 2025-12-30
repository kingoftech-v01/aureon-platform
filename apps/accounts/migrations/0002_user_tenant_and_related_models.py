# Generated for Aureon SaaS Platform
# Adds tenant FK to User and creates UserInvitation and ApiKey

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        # Add tenant FK to User
        migrations.AddField(
            model_name='user',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                help_text='The tenant organization this user belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='users',
                to='tenants.tenant',
            ),
        ),
        # Add index for tenant and role
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['tenant', 'role'], name='accounts_us_tenant__e1f2a3_idx'),
        ),
        # Create UserInvitation model
        migrations.CreateModel(
            name='UserInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(help_text='Email address to send invitation to', max_length=254, verbose_name='Email Address')),
                ('role', models.CharField(choices=[('admin', 'Admin - Full Access'), ('manager', 'Manager - Manage Contracts & Invoices'), ('contributor', 'Contributor - Limited Access'), ('client', 'Client - Portal Access Only')], default='contributor', help_text='Role to assign upon acceptance', max_length=20, verbose_name='Role')),
                ('invitation_token', models.CharField(help_text='Unique token for invitation link', max_length=255, unique=True, verbose_name='Invitation Token')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='pending', max_length=20, verbose_name='Status')),
                ('message', models.TextField(blank=True, help_text='Optional message to include in invitation email', verbose_name='Invitation Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('expires_at', models.DateTimeField(help_text='When the invitation expires', verbose_name='Expires At')),
                ('accepted_at', models.DateTimeField(blank=True, null=True, verbose_name='Accepted At')),
                ('invited_by', models.ForeignKey(help_text='User who sent the invitation', on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(help_text='Tenant organization', on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='tenants.tenant')),
            ],
            options={
                'verbose_name': 'User Invitation',
                'verbose_name_plural': 'User Invitations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='userinvitation',
            index=models.Index(fields=['email', 'status'], name='accounts_us_email_s_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='userinvitation',
            index=models.Index(fields=['tenant', 'status'], name='accounts_us_tenant_s_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='userinvitation',
            index=models.Index(fields=['invitation_token'], name='accounts_us_invitat_g7h8i9_idx'),
        ),
        # Create ApiKey model
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Descriptive name for this API key', max_length=100, verbose_name='Key Name')),
                ('key', models.CharField(help_text='The actual API key (hashed)', max_length=255, unique=True, verbose_name='API Key')),
                ('prefix', models.CharField(help_text='First few characters of key for identification', max_length=10, verbose_name='Key Prefix')),
                ('scopes', models.JSONField(default=list, help_text='List of allowed API scopes/permissions', verbose_name='Scopes')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the API key is active', verbose_name='Active')),
                ('last_used_at', models.DateTimeField(blank=True, help_text='When the key was last used', null=True, verbose_name='Last Used At')),
                ('usage_count', models.PositiveIntegerField(default=0, help_text='Number of times the key has been used', verbose_name='Usage Count')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('expires_at', models.DateTimeField(blank=True, help_text='Optional expiration date', null=True, verbose_name='Expires At')),
                ('user', models.ForeignKey(help_text='User who owns this API key', on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(help_text='Tenant organization', on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='tenants.tenant')),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['key'], name='accounts_ap_key_j0k1l2_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['tenant', 'is_active'], name='accounts_ap_tenant_m3n4o5_idx'),
        ),
    ]
