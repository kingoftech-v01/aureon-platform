# Generated manually for Aureon SaaS Platform

from django.contrib.postgres.fields import JSONField
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='First Name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='Last Name')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff Status')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')),
                ('two_factor_enabled', models.BooleanField(default=False, help_text='Whether two-factor authentication is enabled', verbose_name='2FA Enabled')),
                ('two_factor_secret', models.CharField(blank=True, help_text='TOTP secret key for 2FA', max_length=32, verbose_name='2FA Secret')),
                ('two_factor_backup_codes', models.JSONField(blank=True, default=list, help_text='Backup codes for 2FA recovery', verbose_name='2FA Backup Codes')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'ordering': ['-date_joined'],
            },
        ),
        migrations.CreateModel(
            name='UserInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, verbose_name='Email Address')),
                ('role', models.CharField(choices=[('admin', 'Administrator'), ('member', 'Team Member'), ('viewer', 'Viewer')], default='member', max_length=20, verbose_name='Role')),
                ('token', models.CharField(max_length=100, unique=True, verbose_name='Invitation Token')),
                ('is_accepted', models.BooleanField(default=False, verbose_name='Accepted')),
                ('expires_at', models.DateTimeField(verbose_name='Expires At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_invitations', to='accounts.customuser', verbose_name='Invited By')),
            ],
            options={
                'verbose_name': 'User Invitation',
                'verbose_name_plural': 'User Invitations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='API Key Name')),
                ('key', models.CharField(max_length=100, unique=True, verbose_name='API Key')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='Last Used')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='accounts.customuser', verbose_name='User')),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
                'ordering': ['-created_at'],
            },
        ),
    ]
